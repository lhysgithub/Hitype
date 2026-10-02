import os
import pickle

import numpy as np
from pydantic import BaseModel
from prompt import *
import time
from utils import *
from sklearn.metrics import precision_score, recall_score, f1_score
from openai import OpenAI
from tqdm import tqdm

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
from collections import Counter

failure_cls_client = OpenAI(api_key="", base_url="")
summary_generate_client = OpenAI(api_key="", base_url="")
fault_cls_client = OpenAI(api_key="", base_url="")

path = list[str]


class failure_cls(BaseModel):
    failure_type: str
    chain_of_thought: str


class summary_generate(BaseModel):
    summary: str


class decision(BaseModel):
    fault_type: str
    reason: str


# ====================== 新增：带 Token 统计的 GPT 调用 ======================
def ask_gpt_with_tokens(client, question, conversation_history, response_format):
    messages = conversation_history + [{"role": "user", "content": question}]
    response = client.beta.chat.completions.parse(
        model="gpt-3.5-turbo",
        messages=messages,
        response_format=response_format,
        temperature=0
    )
    result = response.choices[0].message.parsed
    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens
    return result, input_tokens, output_tokens


def inference(data, test_index, data_vector, event_weight, event_tf_idf, failure_types, event_dict, args):
    type_acc = 0
    top_k = []
    sample_count = 0
    predict_type = []
    actual_type = []
    entity_cls_time = 0
    entity_identify_time = 0
    root_cls_time = 0

    # ====================== Token 统计 ======================
    total_input_tokens = 0
    total_output_tokens = 0
    sample_count_tokens = 0

    for k in tqdm(test_index):
        test_sample = data[k]
        if args.entity == "node":
            adj = "None"
        else:
            adj = test_sample["entity_relation"]
        events = test_sample["system_info"]
        failure_type = test_sample["failure_type"]
        root = test_sample["root"]
        entity_diagnose = {}
        entity_text = {}
        event_num = {}

        ################### entity failure identification ##############################
        # for r in list(events.keys())[:args.pod_num]:
        for r in list(events.keys()):
            entity_identify_st = time.time()
            if r not in events.keys():
                continue
            e = events[r]
            items = []
            items = assign_entity_vector(args, e, items, remove=args.remove)
            Flag = False
            for f_type in event_tf_idf.keys():
                type_count = 0
                for item in items:
                    if item in event_tf_idf[f_type].keys():
                        type_count += 1
                if type_count > len(event_tf_idf[f_type]) * args.beta:
                    Flag = True
                    break
            entity_identify_time += time.time() - entity_identify_st

            ################### entity failure classification ##############################
            entity_cls_st = time.time()
            entity_vector = np.zeros(len(event_dict))
            for item in items:
                if item in event_dict.keys():
                    index = event_dict[item]
                    entity_vector[index] += 1
            text = vector_to_text(entity_vector, event_dict)
            entity_text[r] = text
            event_num[r] = entity_vector.sum()
            if not Flag:
                entity_diagnose[r] = "non_failure"
            else:
                similarity, indices = retrieve(entity_vector, np.array(data_vector), event_weight, args.k)
                similarity = np.nan_to_num(similarity, 0)

                sim_types = [failure_types[index] for index in indices[0]]
                sim_text = [vector_to_text(data_vector[index], event_dict) for index in indices[0]]
                sim = [similarity[0][index] for index in indices[0]]
                context_prompt = ""

                for j in range(len(sim_text)):
                    context_prompt += "input:{}".format(sim_text[j])
                    context_prompt += "failure_type:{} similarity: {}\n\n".format(sim_types[j], sim[j])
                context_prompt += "input:{}".format(text) + "failure_type:?"

                answers = []

                if args.dataset == "SN" or args.dataset == "TT":
                    history_context = [
                        {"role": "system", "content": root_classification["failure_cls_{}".format(args.dataset.lower())]}]
                else:
                    history_context = [
                        {"role": "system", "content": root_classification["failure_cls_{}".format(args.entity)]}]

                for _ in range(args.consistency_num):
                    event, i_tokens, o_tokens = ask_gpt_with_tokens(
                        client=failure_cls_client,
                        question=context_prompt,
                        conversation_history=history_context,
                        response_format=failure_cls
                    )
                    answers.append(event.failure_type)
                    history_context.append({"role": "assistant", "content": event.failure_type + " " + event.chain_of_thought})
                    total_input_tokens += i_tokens
                    total_output_tokens += o_tokens

                most_consistent_answer = Counter(answers).most_common(1)[0][0]
                entity_diagnose[r] = most_consistent_answer
                print(f"{r} : diagnose result is {most_consistent_answer}")
                entity_text[r] = text

            entity_cls_time += time.time() - entity_cls_st

        possible_root = []
        system_info = ""
        for p, v in entity_diagnose.items():
            if v != "non_failure":
                possible_root.append(p)
            system_info += "the initial diagnose result of {} is {},and the fault related event number of {} is {}\n".format(p, entity_diagnose[p], p, event_num[p])

        ######################### fault classification ################################
        root_cls_st = time.time()

        if args.entity == "node":
            propagation_context = "Entity Failure Propagation: no information.\n"
        else:
            if args.entity == "pod":
                entity_dict = eval(args.dataset)["pod_dict"]
            elif args.entity == "service":
                entity_dict = eval(args.dataset)["service_dict"]
            id_entity = {v: k for k, v in entity_dict.items()}
            anomaly_entities = possible_root
            anomaly_index = [entity_dict[e] for e in anomaly_entities]
            propagation_context = "Entity Failure Propagation:"
            if args.dataset == "TT":
                adj = np.pad(adj, pad_width=((0, 11), (0, 11)), mode='constant', constant_values=0)
            if args.dataset == "TT":
                adj = np.pad(adj, pad_width=((0, 2), (0, 2)), mode='constant', constant_values=0)
            for j in anomaly_index:
                up_stream = np.where(adj[:, j])[0]
                for up_index in up_stream:
                    if up_index in anomaly_index:
                        call_e = id_entity[up_index]
                        callee = id_entity[j]
                        propagation_context += "{} possibly propagate anomaly to {}.\n".format(callee, call_e)
            if propagation_context == "Entity Failure Propagation:":
                propagation_context += "no information.\n"

        root_classify_prompt = system_info + propagation_context + "\n"
        answers = []

        if args.dataset == "SN" or args.dataset == "TT":
            history_context = [{"role": "system", "content": root_classification["fault_cls_{}".format(args.dataset.lower())]}]
        else:
            history_context = [{"role": "system", "content": root_classification["fault_cls_{}".format(args.entity)]}]

        for _ in range(args.consistency_num):
            event, i_tokens, o_tokens = ask_gpt_with_tokens(
                client=fault_cls_client,
                question=root_classify_prompt,
                conversation_history=history_context,
                response_format=decision
            )
            answers.append(event.fault_type)
            history_context.append({"role": "assistant", "content": event.fault_type + event.reason})
            total_input_tokens += i_tokens
            total_output_tokens += o_tokens

        most_consistent_answer = Counter(answers).most_common(1)[0][0]
        predict_root_type = most_consistent_answer
        root_cls_time += time.time() - root_cls_st

        actual_type.append(failure_type)
        predict_type.append(predict_root_type)

        sample_count += 1
        sample_count_tokens += 1

        # ====================== 【关键】每个样本处理完输出一次累计 Token ======================
        avg_input = total_input_tokens / sample_count_tokens
        avg_output = total_output_tokens / sample_count_tokens
        avg_total = (total_input_tokens + total_output_tokens) / sample_count_tokens

        print(f"\n===== Sample {sample_count_tokens} Finished =====")
        print(f"Cumulative Input Tokens: {total_input_tokens}")
        print(f"Cumulative Output Tokens: {total_output_tokens}")
        print(f"Avg Tokens/Sample: Input={avg_input:.2f}, Output={avg_output:.2f}, Total={avg_total:.2f}")

        # 同时写入文件
        with open(f"./{args.dataset}/result/token_per_sample.txt", "a", encoding="utf-8") as f:
            f.write(f"Sample {sample_count_tokens} | "
                    f"TotalInput={total_input_tokens} | TotalOutput={total_output_tokens} | "
                    f"AvgInput={avg_input:.2f} | AvgOutput={avg_output:.2f} | AvgTotal={avg_total:.2f}\n")

    # ====================== 最终指标 ======================
    precision = precision_score(actual_type, predict_type, average="weighted")
    recall = recall_score(actual_type, predict_type, average="weighted")
    f1 = f1_score(actual_type, predict_type, average="weighted")

    with open("./{}/result/fault_record_summary.txt".format(args.dataset), "a") as f:
        f.write("=" * 60 + "\n")
        f.write("alpha:{}_beta:{}_lamb:{}_k:{}_entity:{}\n".format(args.alpha, args.beta, args.lamb, args.k, args.entity))
        f.write("precision: {:.4f}, recall: {:.4f}, f1: {:.4f}\n".format(precision, recall, f1))
        f.write("Final Total Input Tokens: {}\n".format(total_input_tokens))
        f.write("Final Total Output Tokens: {}\n".format(total_output_tokens))
        f.write("Final Avg Input tokens/sample: {:.2f}\n".format(total_input_tokens / sample_count_tokens))
        f.write("Final Avg Output tokens/sample: {:.2f}\n".format(total_output_tokens / sample_count_tokens))
        f.write("Final Avg Total tokens/sample: {:.2f}\n".format((total_input_tokens + total_output_tokens) / sample_count_tokens))
        f.write("=" * 60 + "\n\n")


def root_cause(args):
    if args.dataset == "SN" or args.dataset == "TT":
        args.entity = "pod"
    with open("./{}/fault_data_llm_{}.pkl".format(args.dataset, args.entity), "rb") as f:
        data = pickle.load(f)
    index = list(data.keys())
    train_data = {}
    train_index = []
    if args.dataset == "SN" or args.dataset == "TT":
        test_index = []
        for k, v in data.items():
            if v["failure_type"] not in train_data.keys():
                train_data[v["failure_type"]] = []

            if v["train_data"] == True:
                if len(train_data[v["failure_type"]]) < 5:
                    train_data[v["failure_type"]].append(v)
                    train_index.append(k)
            elif v["test_data"] == True:
                test_index.append(k)
    else:
        for k, v in data.items():
            if v["failure_type"] not in train_data.keys():
                train_data[v["failure_type"]] = []
            if len(train_data[v["failure_type"]]) < 5:
                train_data[v["failure_type"]].append(v)
                train_index.append(k)
        test_index = list(set(index) - (set(train_index)))

    if os.path.exists("./{}/preprocessed_file/event_idf_{}_{}_{}_{}_{}_{}.pkl".format(args.dataset,args.entity,args.alpha,args.lamb,args.remove,args.step_ratio,args.step_value)):
        with open("./{}/preprocessed_file/tf_idf_data_base_{}_{}_{}_{}_{}_{}.pkl".format(args.dataset, args.entity, args.alpha, args.lamb,args.remove,args.step_ratio,args.step_value), "rb") as f:
            data_vector, event_weight, event_tf_idf, failure_types, event_dict = pickle.load(f)
    else:
        data_vector, event_weight, event_tf_idf, failure_types, event_dict = index_train_data(train_data, args)

    inference(data, test_index, data_vector, event_weight, event_tf_idf, failure_types, event_dict, args)
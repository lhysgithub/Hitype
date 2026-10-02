import numpy as np
import pickle
from tqdm import tqdm
from itertools import combinations
from config_llm import *
from openai import OpenAI
import time
import math
# def ask_gpt(client, question, conversation_history,response_format,max_retries=5):
#     retry_count=0
#     while retry_count < max_retries:
#         try:
#             response = client.beta.chat.completions.parse(
#                 model="gpt-4o-mini",
#                 messages=conversation_history + [{"role": "user", "content": question}],
#                 response_format=response_format,
#                 temperature=0,
#                 seed=2024,
#             )
#             return response.choices[0].message.parsed
#         except Exception as e:
#             print(e)
#             print(f"第{retry_count + 1}次执行失败，进行重试...")
#             retry_count += 1
#             time.sleep(1)
flag=False
def ask_gpt(client, question, conversation_history,response_format,max_retries=5):
    retry_count=0
    while retry_count < max_retries:
        try:
            response = client.beta.chat.completions.parse(
                model="qwen:32b",
                messages=conversation_history + [{"role": "user", "content": question}],
                response_format=response_format,
                temperature=0,
                seed=2024,
            )
            return response.choices[0].message.parsed
        except Exception as e:
            print(e)
            print(f"第{retry_count + 1}次执行失败，进行重试...")
            retry_count += 1
            time.sleep(1)





def vector_to_text(vector,event_dict):
    text=""
    id_event={v:k for k,v in event_dict.items()}
    for j in range(len(vector)):
        if vector[j] >0:
            text+=id_event[j]+" \n"
    return text

def evaluate(topk, sample_count,training=True):
    top_value = [0] * 10
    for top in topk:
        for i in range(top - 1, 10):
            top_value[i] += 1
    top_prob = np.array(top_value) / sample_count
    avg_5 = np.array(top_prob[:5]).mean()
    result = {"top1": top_prob[0], "top3": top_prob[2], "top5": top_prob[4], "avg5": avg_5}
    return result


def retrieve(vector, data_vector,event_weight=None, k=5):
    vectors_a = np.array(vector).reshape(1, -1)
    vectors_b = np.array(data_vector)
    if event_weight is not None:
        event_weight=np.array(list(event_weight.values()))
        # 计算点积
        dot_product =np.dot(vectors_a*event_weight,vectors_b.T)
        norm_a = np.linalg.norm(vectors_a * event_weight, axis=1, keepdims=True)
        norm_b = np.linalg.norm(vectors_b, axis=1, keepdims=True)
    else:
        dot_product = np.dot(vectors_a , vectors_b.T)
        norm_a = np.linalg.norm(vectors_a, axis=1, keepdims=True)
        norm_b = np.linalg.norm(vectors_b, axis=1, keepdims=True)


    # 计算余弦相似度矩阵
    similarity_matrix = dot_product / (norm_a * norm_b.T)

    # 对于每个向量，找出相似度最高的top_k个向量的索引
    indices = np.argsort(-similarity_matrix, axis=1)[:, :k]

    return similarity_matrix, indices



def _extract_stat_features(
    value, stat_name, stat_fn,
    scope_ratio,    # 增长率阈值 0~1
    scope_value,    # 增长值阈值 >1
    prefix, m, cumulate
):
    before = stat_fn(value[:5])
    after = stat_fn(value[5:])
    result = []

    if before > 0:
        increase = (after - before) / before
        decrease = (before - after) / before

        # ===================== 增长率：只使用 0~1 的阈值 =====================
        for direction, ratio in [("increase", increase), ("decrease", decrease)]:
            if ratio > 0:
                for s in scope_ratio:
                    if ratio > s:
                        result.append(f"{prefix}{m} {stat_name}_{direction}_{s}")
                        if not cumulate:
                            break
    else:
        # ===================== 增长值：只使用 >1 的阈值 =====================
        increase = 0
        decrease = 0
        for s in scope_value:
            if after > s:
                result.append(f"{prefix}{m} {stat_name}_increase {s} from 0")
                if not cumulate:
                    break

    return result


def assign_entity_vector(args, e, items, up=False, down=False, cumulate=True, remove=""):
    prefix = ""
    if up:
        prefix = "upstream:"
    elif down:
        prefix = "downstream:"

    if len(e[0]) > 0:
        if type(e[0]) == dict:
            for l, value in e[0].items():
                items.append(prefix + l)
        else:
            for l in e[0]:
                items.append(prefix + l)

    # ===================== 1. 增长率阈值：0~1 等差 =====================
    STEP_LINEAR = args.step_ratio
    growth_rate_part = []
    current = 0.0
    while current <= 10.0 + 1e-9:
        growth_rate_part.append(round(current, 4))
        current += STEP_LINEAR
    scope_ratio = [v for v in growth_rate_part if v <= 10.0]

    # ===================== 2. 增长值阈值：>1 等比 =====================
    STEP_RATIO = args.step_value
    MAX_VALUE = 1e5
    growth_value_part = []
    current = 1.0 * STEP_RATIO
    while current <= MAX_VALUE:
        growth_value_part.append(current)
        current *= STEP_RATIO
    scope_value = growth_value_part

    global flag
    if not flag:
        print("增长率阈值 (0~1):", scope_ratio)
        print("增长值阈值 (>1):", scope_value)
        flag = True

    stat_configs = [
        ("max", np.max),
        ("min", np.min),
        ("std", np.std),
        ("mean", np.mean),
    ]

    if len(e[1]) > 0 or len(e[2]) > 0:
        for m, value in e[1].items():
            value = np.nan_to_num(value, nan=0)
            m = ''.join([c for c in m if not c.isdigit()])
            for stat_name, stat_fn in stat_configs:
                if remove == stat_name:
                    continue
                items.extend(
                    _extract_stat_features(
                        value, stat_name, stat_fn,
                        scope_ratio,    # 传入增长率阈值
                        scope_value,    # 传入增长值阈值
                        prefix, m, cumulate
                    )
                )
    return items


def index_train_data(train_data, args):

    pod_dict = eval(args.dataset)["pod_dict"]
    event_tf_idf = {}
    failure_types=[]
    data_vector=[]



    for k in train_data.keys():
        failure_events={}
        non_failure_events={}
        non_failure_count=0
        failure_count=0
        for v in train_data[k]:
            events = v["system_info"]
            failure_type = v["failure_type"]
            root = v["root"]
            for p , e in events.items():
                items = []
                items = assign_entity_vector(args,e, items, remove=args.remove)
                # new_items = [' and '.join(pair) for pair in combinations(items, 2)]
                # items += new_items
                items=list(set(items))
                if p==root:
                    for item in items:
                        if item not in failure_events:
                            failure_events[item]=1
                        else:
                            failure_events[item]+=1
                    failure_count+=1
                else:

                    for item in items:
                        if item not in non_failure_events:
                            non_failure_events[item]=1
                        else:
                            non_failure_events[item]+=1
                    non_failure_count+=1
        for other in tqdm(train_data.keys()):
            if other==k:
                continue
            else:
                for v in train_data[k]:
                    events = v["system_info"]
                    failure_type = v["failure_type"]
                    root = v["root"]
                    for p, e in events.items():

                        items = []
                        items = assign_entity_vector(args,e, items, remove=args.remove)
                        # new_items = [' and '.join(pair) for pair in combinations(items, 2)]
                        # items += new_items
                        items = list(set(items))
                        for item in items:
                            if item not in non_failure_events:
                                non_failure_events[item] = 1
                            else:
                                non_failure_events[item] += 1
                        non_failure_count+=1
        for e,v in failure_events.items():
            tf_idf=(v/failure_count)* np.log(non_failure_count/(non_failure_events[e]+1))
            if (v/failure_count) <args.alpha:
                tf_idf=0
            failure_events[e]=tf_idf
        event_tf_idf[k]=failure_events

    with open("./{}/preprocessed_file/event_idf_{}_{}_{}_{}_{}_{}.pkl".format(args.dataset,args.entity,args.alpha,args.lamb,args.remove,args.step_ratio,args.step_value), "wb") as f:
        pickle.dump((event_tf_idf), f)

    with open("./{}/preprocessed_file/event_idf_{}_{}_{}_{}_{}_{}.pkl".format(args.dataset,args.entity,args.alpha,args.lamb,args.remove,args.step_ratio,args.step_value), "rb") as f:
        event_tf_idf=pickle.load(f)
    # for k, v in event_tf_idf.items():

    #     filtered_dict = dict(sorted(v.items(), key=lambda item: item[1], reverse=True)[:args.lamb])

    #     filtered_dict={key: v  for key, v in filtered_dict.items() if v > 0  }
    #     event_tf_idf[k]=filtered_dict

    for k, v in event_tf_idf.items():
        # 1. 先取 TF-IDF 最高的一批候选
        sorted_items = sorted(v.items(), key=lambda x: x[1], reverse=True)
        candidates = sorted_items[: args.lamb * 3]

        # 2. 按 (指标名, 趋势) 分组，每组保留加权分数最高的
        groups = {}
        for event_str, tfidf in candidates:
            if tfidf <= 0:
                continue

            val = 0.0
            base = event_str
            trend = "none"

            # 解析 increase
            if "_increase_" in event_str:
                base, val_str = event_str.split("_increase_")
                trend = "increase"
                try:
                    val = float(val_str)
                except:
                    continue

            # 解析 decrease
            elif "_decrease_" in event_str:
                base, val_str = event_str.split("_decrease_")
                trend = "decrease"
                try:
                    val = float(val_str)
                except:
                    continue

            # ===================== 核心加权公式 =====================
            combined_score = tfidf * (1.0 + val)
            key = (base, trend)

            # 同组只保留分数最高的
            if key not in groups or combined_score > groups[key]["score"]:
                groups[key] = {
                    "event": event_str,
                    "tfidf": tfidf,
                    "val": val,
                    "score": combined_score
                }

        # 3. 按融合分数排序，取前 args.lamb 个
        retained = sorted(groups.values(), key=lambda x: x["score"], reverse=True)
        filtered_dict = {item["event"]: item["tfidf"] for item in retained[:args.lamb]}

        event_tf_idf[k] = filtered_dict
        print("{}:{}".format(k,filtered_dict))




    count=0
    event_dict={}
    tf_idf={}
    event_weight={}

    for k,v in event_tf_idf.items():

        for e in v.keys():
            if e not in event_dict:
                event_dict[e]=count
                count+=1
                tf_idf[e]=v[e]

            else:
                event_dict.pop(e)
                tf_idf.pop(e)
    event_dict={ list(event_dict.keys())[j]:j for j in range(len(event_dict))}
    for k,v in event_dict.items():
        event_weight[k]=tf_idf[k]

    for k in train_data.keys():

        for v in train_data[k]:
            events = v["system_info"]
            failure_type = v["failure_type"]
            root = v["root"]
            e=events[root]
            items = []
            items = assign_entity_vector(args,e, items, remove=args.remove)
            # new_items = [' and '.join(pair) for pair in combinations(items, 2)]
            # items += new_items
            pod_vec=np.zeros(len(event_dict))
            for item in items:
                if item in event_dict.keys():
                    # if item in event_tf_idf[failure_type].keys():
                    index=event_dict[item]
                    pod_vec[index]=1

            data_vector.append(pod_vec)
            failure_types.append(failure_type)

    with open("./{}/preprocessed_file/tf_idf_data_base_{}_{}_{}_{}_{}_{}.pkl".format(args.dataset,args.entity,args.alpha,args.lamb,args.remove,args.step_ratio,args.step_value), "wb") as f:
        pickle.dump((data_vector,event_weight,event_tf_idf,failure_types,event_dict),f)



    return data_vector,event_weight,event_tf_idf,failure_types,event_dict

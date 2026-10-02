import pickle
from config_llm import *
import argparse
import numpy as np
from mr_rca import root_cause
import random
import os
import json




def seed_everything(seed=2024):
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)



def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


parser = argparse.ArgumentParser()
parser.add_argument('-m', '--method', type=str, default="MR_RCA",
                    choices=["MR_RCA" ], help="method choice")
parser.add_argument('-d', '--dataset', type=str, default="AIops2022",
                    choices=["SN", "AIops2022","TT"],
                    help="dataset choice")

parser.add_argument('-e', '--entity', type=str, default="service",
                    choices=["pod", "node","service"],
                 )

parser.add_argument('-r', '--remove',type=str,default=" ",choices=[" ","min","max","mean","std"])

#########################hyperparameter experiment######

parser.add_argument('-t', '--beta', type=float, default=0.7,
                  )

parser.add_argument( '--step_ratio', type=float, default=0.05,
                  )
parser.add_argument( '--step_value', type=float, default=10,
                  )
parser.add_argument('--alpha', type=float, default=0.6,
                    )
parser.add_argument('--k', type=int, default=3)

parser.add_argument('--lamb', type=int, default=20,
                    )   # default 60 

parser.add_argument('--consistency_num', type=int, default=1
                    )

seed_everything()
args = parser.parse_args()
print(args)

result = root_cause(args)


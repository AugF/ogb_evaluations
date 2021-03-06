'''
改文件是为了画耗时比例随着Batch Size变化的图像
'''
# coding=utf-8
import os
import sys
import re
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

from utils import batch_sizes, relative_precent, batches_per_epoch
plt.style.use("ggplot")
plt.rcParams["font.size"] = 12

os.chdir("/home/wangzhaokang/wangyunpan/gnns-project/ogb_evaluations/exp")

def survey(labels, data, category_names, ax=None, color_dark2=False): # stages, layers, steps，算子可以通用
    # labels: 这里是纵轴的坐标; 
    # data: 数据[[], []] len(data[1])=len(category_names); 
    # category_names: 比例的种类
    for i, c in enumerate(category_names):
        if c[0] == '_':
            category_names[i] = c[1:]

    data_cum = data.cumsum(axis=1)
    if color_dark2:
        category_colors = plt.get_cmap('Dark2')(
            np.linspace(0.15, 0.85, data.shape[1]))
    else:
        category_colors = plt.get_cmap('RdYlGn')(
            np.linspace(0.15, 0.85, data.shape[1]))       
        
    if ax is None:
        fig, ax = plt.subplots(figsize=(9.2, 5))
    else:
        fig = None
    ax.invert_yaxis()
    #ax.xaxis.set_visible(False)
    ax.set_xlim(0, np.sum(data, axis=1).max())
    ax.set_xlabel("Proportion (%)")

    for i, (colname, color) in enumerate(zip(category_names, category_colors)):
        widths = data[:, i]
        starts = data_cum[:, i] - widths
        ax.barh(labels, widths, left=starts, height=0.5,
                label=colname, color=color)
        xcenters = starts + widths / 2

        r, g, b, _ = color
        text_color = 'white' if r * g * b < 0.5 else 'darkgrey'
        for y, (x, c) in enumerate(zip(xcenters, widths)):
            ax.text(x, y, '%.1f' % c, ha='center', va='center',
                    color=text_color)
    ax.legend(ncol=len(category_names), bbox_to_anchor=(0, 1),
              loc='lower left', fontsize='small')

    return fig, ax

def pics_proportion(dir_in="log", file_type="png"):
    dir_out = "res"
    
    ylabel = f"Training Time per Batch(ms)"
    xlabel = f"Relative Batch Size (%)"

    for file_name in batch_sizes.keys():
        file_path = f"{dir_in}/{file_name}"
        xticklabels = [str(i) + '%' for i in relative_precent[file_name]]
        batches = batches_per_epoch[file_name]
        fail = False
        df_data = []
        for i, bs in enumerate(batch_sizes[file_name]):
            log_path = file_path + '_' + str(bs) + ".out"
            if not os.path.exists(log_path): # 文件不存在
                fail = True 
                continue 
            print(log_path)
            train_time, sampling_time, to_time = 0.0, 0.0, 0.0
            success = False
            with open(log_path) as f:
                for line in f:
                    match_line = re.match(r"Avg_sampling_time: (.*)s, Avg_to_time: (.*)s,  Avg_train_time: (.*)s", line)
                    if match_line:
                        sampling_time = float(match_line.group(1))
                        to_time = float(match_line.group(2))
                        train_time = float(match_line.group(3))
                        success = True
                        break
            # 转化为ms
            if not success: 
                fail = True
                break
            
            sampling_time /= batches[i]
            to_time /= batches[i]
            train_time /= batches[i]
            df_data.append([sampling_time, to_time, train_time])
            print(f"bs: {bs}, training time: {sampling_time+to_time+train_time}s")
        
        if fail: continue #
        df_data = np.array(df_data)
        # np.savetxt(dir_out + "/" + file_name + ".csv", df_data)
        df_data = 100 * df_data / df_data.sum(axis=1).reshape(-1, 1)
        # print(df_data)
        fig, ax = survey(xticklabels[:df_data.shape[0]], df_data, ['Sampling', 'Data Transferring', 'Training'], color_dark2=True)
        ax.set_title(file_name, loc="right")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        plt.tight_layout()
        fig.savefig(dir_out + "/proportion_bar/" + file_name + "." + file_type)
        

def pics_stack(dir_in="log", dir_out = "res"):
    
    ylabel = f"Training Time per Batch (s)"
    xlabel = f"Relative Batch Size (%)"
    
    if not os.path.exists(f"{dir_out}/sampling_time"):
        os.makedirs(f"{dir_out}/sampling_time")
        
    if not os.path.exists(f"{dir_out}/sampling_info"):
        os.makedirs(f"{dir_out}/sampling_info")
    
    if not os.path.exists(f"{dir_out}/stack_bar"):
        os.makedirs(f"{dir_out}/stack_bar")
        
    for file_name in batch_sizes.keys():
        file_path = f"{dir_in}/{file_name}"
        xticklabels = [str(i) + '%' for i in relative_precent[file_name]]
        batches = batches_per_epoch[file_name]
        fail = False
        
        df_data = []
        df_info = []
        for i, bs in enumerate(batch_sizes[file_name]):
            log_path = file_path + '_' + str(bs) + ".out"
            if not os.path.exists(log_path): # 文件不存在
                fail = True 
                continue 
            print(log_path)
            train_time, sampling_time, to_time = 0.0, 0.0, 0.0
            acc = 0.0
            success = False
            with open(log_path) as f:
                for line in f:
                    match_line = re.match(r"Avg_sampling_time: (.*)s, Avg_to_time: (.*)s,  Avg_train_time: (.*)s", line)
                    acc_line = re.match(r".*Final Test: (.*) ± nan", line)
                    if match_line:
                        sampling_time = float(match_line.group(1))
                        to_time = float(match_line.group(2))
                        train_time = float(match_line.group(3))
                        success = True
                    if acc_line:
                        acc = float(acc_line.group(1))
            # 转化为s
            if not success: 
                fail = True
                break
            
            time_per_epoch = sampling_time+to_time+train_time
            print(f"acc: {acc}")
            print(f"bs: {bs}, training time per epoch: {time_per_epoch}s")
            
            sampling_time /= batches[i]
            to_time /= batches[i]
            train_time /= batches[i]
            time_per_batch = sampling_time+to_time+train_time
            print(f"bs: {bs}, training time per batch: {time_per_batch}s")
            df_data.append([sampling_time, to_time, train_time])
            df_info.append([bs, time_per_batch, time_per_epoch, acc])
        
        if fail: continue #
        
        # 保存数据
        df_data = np.array(df_data)
        sampling_ratio = 100 * df_data[:, 0] / df_data.sum(axis=1)
        np.savetxt(f"{dir_out}/sampling_time/" + file_name + ".csv", df_data)
        pd.DataFrame(df_info, index=xticklabels, columns=["Len(Train Loader)", "Avg Batch Time(s)", "Avg Epoch Time(s)", "Acc"]).to_csv(f"{dir_out}/sampling_info/{file_name}.csv")
        
        # 绘制图像
        colors = plt.get_cmap('Dark2')(
            np.linspace(0.15, 0.85, 5)) 
        fig, ax = plt.subplots()

        ax.bar(xticklabels, df_data[:, 2], alpha=0.6,  facecolor = colors[2], lw=1, label='Training')
        ax.bar(xticklabels, df_data[:, 1], bottom=df_data[:, 2], alpha=0.6,  facecolor = colors[1], lw=1, label='Data Tranfering')
        rects = ax.bar(xticklabels, df_data[:, 0], bottom=[df_data[i][1] + df_data[i][2] for i in range(df_data.shape[0])], alpha=0.6,  facecolor = colors[0],  lw=1, label='Sampling')
        
        for i, rect in enumerate(rects):
            ax.text(rect.get_x() + rect.get_width() / 3, rect.get_y() + rect.get_height() / 3, '%.1f' % sampling_ratio[i])

        ax.set_ylabel(ylabel)
        ax.set_xlabel(xlabel)
        ax.legend()#图例展示位置，数字代表第几象限
        fig.savefig(f"{dir_out}/stack_bar/" + file_name + ".png")
        print("\n")


def pics_stack_full(dir_in="log_full", dir_out = "res_full"):
    outliers = ['mag_neighborsampling_rgcn', 'products_graphsaint_sage']  
    
    ylabel = f"Training Time per Batch (s)"
    xlabel = f"Relative Batch Size (%)"
    
    if not os.path.exists(f"{dir_out}/sampling_time"):
        os.makedirs(f"{dir_out}/sampling_time")
        
    if not os.path.exists(f"{dir_out}/sampling_info"):
        os.makedirs(f"{dir_out}/sampling_info")
    
    if not os.path.exists(f"{dir_out}/stack_bar"):
        os.makedirs(f"{dir_out}/stack_bar")
        
    for file_name in batch_sizes.keys():
        file_path = f"{dir_in}/{file_name}"
        xticklabels = [str(i) + '%' for i in relative_precent[file_name]]
        batches = batches_per_epoch[file_name]
        fail = False
        
        df_data = []
        df_info = []
        for i, bs in enumerate(batch_sizes[file_name]):
            log_path = file_path + '_' + str(bs) + ".out"
            if not os.path.exists(log_path): # 文件不存在
                fail = True 
                continue 
            print(log_path)
            train_time, sampling_time, to_time = 0.0, 0.0, 0.0
            acc = 0.0
            success = False
            with open(log_path) as f:
                for line in f:
                    match_line = re.match(r"Avg_sampling_time: (.*)s, Avg_to_time: (.*)s,  Avg_train_time: (.*)s", line)
                    acc_line = re.match(r".*Final Test: (.*) ± nan", line)
                    if match_line:
                        sampling_time = float(match_line.group(1))
                        to_time = float(match_line.group(2))
                        train_time = float(match_line.group(3))
                        success = True
                    if acc_line:
                        acc = float(acc_line.group(1))
            # 转化为s
            if not success: 
                fail = True
                break
            
            if file_name in outliers:
                time_per_epoch = sampling_time+to_time+train_time
                print(f"acc: {acc}")
                print(f"bs: {bs}, training time per epoch: {time_per_epoch}s")
                
                sampling_time /= batches[i]
                to_time /= batches[i]
                train_time /= batches[i]
                time_per_batch = sampling_time + to_time + train_time
                print(f"bs: {bs}, training time per batch: {time_per_batch}s")
                df_data.append([sampling_time, to_time, train_time, 100 * sampling_time / time_per_batch])
                df_info.append([bs, time_per_batch, time_per_epoch, acc])
            else:
                time_per_batch = sampling_time + to_time + train_time
                time_per_epoch = time_per_batch * batches[i]
                df_data.append([sampling_time, to_time, train_time, 100 * sampling_time / time_per_batch])
                df_info.append([bs, time_per_batch, time_per_epoch, acc])
                
        if fail: continue #
        
        # 保存数据
        df_data = np.array(df_data)
        sampling_ratio = 100 * df_data[:, 0] / df_data.sum(axis=1)
        pd.DataFrame(df_data, index=xticklabels, columns=["Sampling", "Data Transfering", "Training", "Sampling Ratio"]).to_csv(f"{dir_out}/sampling_time/" + file_name + ".csv")
        pd.DataFrame(df_info, index=xticklabels, columns=["Len(Train Loader)", "Avg Batch Time(s)", "Avg Epoch Time(s)", "Acc"]).to_csv(f"{dir_out}/sampling_info/{file_name}.csv")
        
        # 绘制图像
        colors = plt.get_cmap('Dark2')(
            np.linspace(0.15, 0.85, 5)) 
        fig, ax = plt.subplots()

        ax.bar(xticklabels, df_data[:, 2], alpha=0.6,  facecolor = colors[2], lw=1, label='Training')
        ax.bar(xticklabels, df_data[:, 1], bottom=df_data[:, 2], alpha=0.6,  facecolor = colors[1], lw=1, label='Data Transferring')
        rects = ax.bar(xticklabels, df_data[:, 0], bottom=[df_data[i][1] + df_data[i][2] for i in range(df_data.shape[0])], alpha=0.6,  facecolor = colors[0],  lw=1, label='Sampling')
        
        for i, rect in enumerate(rects):
            ax.text(rect.get_x() + rect.get_width() / 3, rect.get_y() + rect.get_height() / 3, '%.1f' % df_data[:,3][i])

        ax.set_ylabel(ylabel)
        ax.set_xlabel(xlabel)
        ax.legend()#图例展示位置，数字代表第几象限
        fig.savefig(f"{dir_out}/stack_bar/" + file_name + ".png")
        print("\n")

pics_stack_full()
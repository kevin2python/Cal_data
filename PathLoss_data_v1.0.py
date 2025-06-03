# Version: V1.0
# Description: Process and analyze calibration data from CSV files
# Author: eostvxb
# Date: 2025
#### TX 频谱仪线损源文件是 0.csv-7.csv
#### TX 功率计线损源文件是 00.csv-07.csv
#### RX 频谱仪线损源文件是 RX0.csv-RX7.csv

import os
import matplotlib.pyplot as plt
import numpy as np

def process_file(file_path):
    # 读取文件内容
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # 找到数据开始的行
    start_idx = 0
    for i, line in enumerate(lines):
        if line.strip() == 'Freq(Hz),S21(DB),S21(DEG)':
            start_idx = i + 1
            break
    
    # 提取数据行
    data_lines = []
    for line in lines[start_idx:]:
        if line.strip():
            parts = line.strip().split(',')
            if len(parts) >= 2:
                freq = parts[0]
                db = f"{float(parts[1]):.2f}"  # 保留2位小数
                data_lines.append(f"{freq},{db}")
    
    return data_lines

def save_processed_data(data_lines, output_file):
    # 创建目标文件的目录（如果不存在）
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    # 保存数据到文件
    with open(output_file, 'w') as f:
        f.write('\n'.join(data_lines))
    
    # 如果文件名以SG1_开头，创建对应的SG2_文件
    if os.path.basename(output_file).startswith('SG1_'):
        sg2_file = os.path.join(
            os.path.dirname(output_file),
            'SG2_' + os.path.basename(output_file)[4:]
        )
        with open(sg2_file, 'w') as f:
            f.write('\n'.join(data_lines))

def get_output_filenames(source_file):
    # 从源文件名提取数字
    base_name = source_file.split('.')[0]
    
    # 处理不同类型的文件
    if base_name.startswith('RX'):
        # RX类文件
        num = int(base_name[2:])  # 获取RX后的数字
        letter = chr(65 + num)  # 将数字转换为对应的字母 (0->A, 1->B, etc)
        return [
            f'SG1_RX{letter}.txt',
            f'SG2_RX{letter}.txt',
            f'SG1_RXA{num+1}.txt',
            f'SG2_RXA{num+1}.txt'
        ]
    
    elif len(base_name) == 1:
        # 一位数文件 (如0.csv, 1.csv等)
        num = int(base_name)
        letter = chr(65 + num)  # 将数字转换为对应的字母 (0->A, 1->B, etc)
        return [f'TX{letter}_NF_SPEC.txt', f'TXA{num+1}_NF_SPEC.txt']
    
    elif len(base_name) == 2:
        # 两位数文件 (如00.csv, 01.csv等)
        mapping = {
            '00': 'A',
            '01': 'B',
            '02': 'C',
            '03': 'D',
            '04': 'E',
            '05': 'F',
            '06': 'G',
            '07': 'H'
        }
        letter = mapping.get(base_name)
        if letter:
            return [f'TX{letter}_NF_OSC.txt']
    
    return []

def plot_comparison(file_groups):
    # 为每种类型的文件创建一个图
    for file_type, files in file_groups.items():
        plt.figure(figsize=(12, 6))
        
        # 获取所有可能的文件名
        if file_type == 'NF_SPEC':
            target_files = [f'TX{chr(65+i)}_NF_SPEC.txt' for i in range(8)]  # TXA到TXH
        elif file_type == 'RX':
            target_files = [f'SG1_RX{chr(65+i)}.txt' for i in range(8)]  # SG1_RXA到SG1_RXH
        elif file_type == 'NF_OSC':
            target_files = [f'TX{chr(65+i)}_NF_OSC.txt' for i in range(8)]  # TXA到TXH
        else:
            continue
        
        # 遍历所有可能的文件名
        for target_file in target_files:
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), target_file)
            if os.path.exists(file_path):
                # 读取数据
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                
                freqs = []
                dbs = []
                for line in lines:
                    parts = line.strip().split(',')
                    if len(parts) == 2:
                        freqs.append(float(parts[0]))
                        dbs.append(float(parts[1]))
                
                # 绘制曲线
                label = os.path.basename(file_path)
                plt.plot(freqs, dbs, label=label)
        
        plt.title(f'{file_type} Comparison')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Pathloss (dB)')
        plt.grid(True)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
        # 保存图片
        plt.savefig(f'{file_type}_comparison.png')
        plt.close()

def main():
    folder_path = os.path.dirname(os.path.abspath(__file__))
    
    # 配置日志
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    try:
        # 获取所有csv文件
        csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
        if not csv_files:
            logging.warning("未找到CSV文件")
            return
        
        file_groups = {'RX': [], 'NF_SPEC': [], 'NF_OSC': []}
        
        # 处理所有文件
        for source_file in csv_files:
            source_path = os.path.join(folder_path, source_file)
            target_files = get_output_filenames(source_file)
            
            if not target_files:
                logging.info(f"跳过文件 {source_file} - 不符合命名规则")
                continue
                
            try:
                processed_lines = process_file(source_path)
                
                for target_file in target_files:
                    target_path = os.path.join(folder_path, target_file)
                    save_processed_data(processed_lines, target_path)
                    logging.info(f"已处理 {source_file} -> {target_file}")
                    
                    # 使用字典实现更简洁的分组逻辑
                    for group_name in file_groups:
                        if group_name in target_file:
                            file_groups[group_name].append(target_path)
                            break
                            
            except Exception as e:
                logging.error(f"处理文件 {source_file} 时出错: {str(e)}")
        
        # 绘制对比图
        plot_comparison(file_groups)
        logging.info("已生成所有对比图")
        
    except Exception as e:
        logging.error(f"程序执行出错: {str(e)}")

if __name__ == '__main__':
    main()
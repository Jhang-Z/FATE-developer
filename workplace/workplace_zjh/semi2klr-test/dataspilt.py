import csv

# 输入文件路径和名称
input_file = './breast_hetero_guest.csv'
# 输出文件1路径和名称
output_file1 = './train_data_guest.csv'
# 输出文件2路径和名称
output_file2 = './test_data_guest.csv'

# 打开输入文件和输出文件
with open(input_file, 'r', newline='') as file_in, open(output_file1, 'w', newline='') as file_out1, open(output_file2, 'w', newline='') as file_out2:
    # 创建CSV读取器和写入器
    reader = csv.reader(file_in)
    writer1 = csv.writer(file_out1)
    writer2 = csv.writer(file_out2)

    # 读取表头
    header = next(reader)

    # 写入表头到输出文件
    writer1.writerow(header)
    writer2.writerow(header)

    # 将数据分割为两个文件
    data = list(reader)
    split_index = 284
    data1 = data[:split_index]
    data2 = data[split_index:]

    # 写入数据到输出文件
    writer1.writerows(data1)
    writer2.writerows(data2)
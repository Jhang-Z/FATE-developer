import csv

def output_first_n_rows_with_header(input_file, output_file, n):
    with open(input_file, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            header = next(reader)  
            writer.writerow(header)  
            for i, row in enumerate(reader):
                if i >= n:
                    break
                writer.writerow(row)


input_file = './1000_300_test.csv'
output_file = 'test_guest.csv'
rows_to_keep = 5000

output_first_n_rows_with_header(input_file, output_file, rows_to_keep)
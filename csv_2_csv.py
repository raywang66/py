import csv

mat_res = dict()


def read_spreadsheet_res():
    global mat_res

    f = open("spreadsheet_res2.txt", "r")
    _content = f.read().split("\n")
    i = 0
    while i < len(_content):
        if len(_content[i].strip()) != 0:
            _line_splitted = _content[i].split(" ")
            if len(_line_splitted) == 7:
                _mat_name =_line_splitted[6]
                print(_mat_name)
                mat_res[_mat_name] = []
                while i < len(_content)-1:
                    i += 1
                    if len(_content[i].strip()) != 0:
                        if ">>" in _content[i] or "ERROR" in _content[i]:
                            print(i)
                            pass
                        else:
                            print(_content[i])
                            mat_res[_mat_name].append(_content[i])
                    else:
                        break
        i += 1

    return


def read_brcm_summary_csv():
    global mat_res

    csv_file_name = "summary.csv"
    data = csv.reader(open(csv_file_name))
    header = next(data)
    print(header)
    rows = []
    rows_res = []
    header_doubled = [""]
    for row in data:
        print(row)
        rows.append(row)

    for col in range(0, len(header)):
        if len(header[col]) == 0:
            continue

        print(f"{col}: {header[col]}")
        _old_header = header[col]
        x = _old_header.find("Tc")
        y = _old_header.find(".mat")
        _new_header = _old_header[x:y] + "_" + _old_header[0:x] + _old_header[y:]

        header_doubled.append(_old_header)
        # header_doubled.append(f"LP_{_new_header}")
        header_doubled.append(f"LP")

        for row in range(0, len(rows)-1):
            if row > len(rows_res)-1:
                rows_res.append([""]*len(rows[row]))
            else:
                pass

            if col == 0:
                rows_res[row][col] = rows[row][col]
            else:
                if row == 0:
                    pass
                else:
                    if False:   #len(mat_res[_new_header]) < 10:
                        print("Error")
                    else:
                        rows_res[row][col] = mat_res[_new_header][row-1]

            print(f"{row},{col}: {rows[row][col]}, {rows_res[row][col]}")

    pass

    with open("summary_res.csv", 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header_doubled)
        _row_new = []
        for row in range(0, len(rows)):
            _row_new.append([])
            for col in range(0, len(rows[row])):
                _row_new[row].append(rows[row][col])
                if col == 0:
                    pass
                elif row < len(rows_res):
                    _row_new[row].append(rows_res[row][col])
                else:
                    _row_new[row].append("")
            print(_row_new[row])
            writer.writerow(_row_new[row])

    pass


if __name__ == '__main__':
    read_spreadsheet_res()
    read_brcm_summary_csv()

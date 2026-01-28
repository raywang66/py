import csv
import random

csv_dict_list = []


def read_csv_2_dict():
    global csv_dict_list

    csv_file_name = "IQsniffer_unittest_results_2e_100loops.csv"
    with open(csv_file_name) as csvfile:
        reader = csv.DictReader(csvfile)
        time_stamp = "Not started"
        list_index = -1
        csv_dict = {}
        for row in reader:

            vsaIndex = row['vsaIndex']
            macAddress2 = row['macAddress2']
            packetSubtype= row['packetSubtype']
            macAddress1 = row['macAddress1']
            preamblePower = row['preamblePower']

            if time_stamp != row['TimeStamp']:
                time_stamp = row['TimeStamp']
                if len(csv_dict) > 0:
                    csv_dict_list.append(csv_dict)
                csv_dict = {}

            if vsaIndex not in csv_dict.keys():
                csv_dict[vsaIndex] = {macAddress2: {packetSubtype: {macAddress1: [preamblePower]}}}
            elif macAddress2 not in csv_dict[vsaIndex].keys():
                csv_dict[vsaIndex][macAddress2] = {packetSubtype: {macAddress1: [preamblePower]}}
            elif packetSubtype not in csv_dict[vsaIndex][macAddress2].keys():
                csv_dict[vsaIndex][macAddress2][packetSubtype] = {macAddress1: [preamblePower]}
            elif macAddress1 not in csv_dict[vsaIndex][macAddress2][packetSubtype].keys():
                csv_dict[vsaIndex][macAddress2][packetSubtype][macAddress1] = [preamblePower]
            else:
                # the key combinations yield more than one values
                csv_dict[vsaIndex][macAddress2][packetSubtype][macAddress1].append(preamblePower)

        print(csv_dict_list)

    pass


def compare_2_csv():
    for i in range(1000):
        # generate two random numbers within [0,99]
        # first_csv = random.randrange(0, 99, 1)
        # second_csv = random.randrange(0, 99, 1)
        first_csv = 5
        second_csv = 78
        if first_csv == second_csv:
            continue
        else:
            print(f"{first_csv} vs {second_csv}")
            dict1 = csv_dict_list[first_csv]
            dict2 = csv_dict_list[second_csv]

            for vsaIndex in dict1.keys():
                for macAddress2 in dict1[vsaIndex].keys():
                    for packetSubtype in dict1[vsaIndex][macAddress2].keys():
                        for macAddress1 in dict1[vsaIndex][macAddress2][packetSubtype].keys():
                            print(f"vsaIndex:{vsaIndex}, "
                                  f"macAddress2:{macAddress2}, "
                                  f"packetSubtype:{packetSubtype}, "
                                  f"macAddress1:{macAddress1}")
                            if macAddress2 == "N/A" and packetSubtype == "N/A" and macAddress1 == "N/A":
                                # CRC failed, need special logic
                                continue
                            else:
                                power1 = dict1[vsaIndex][macAddress2][packetSubtype][macAddress1]
                                # dict2 must have the same hierarchy, otherwise the algorithm fails
                                power2 = dict2[vsaIndex][macAddress2][packetSubtype][macAddress1]
                                print(f"first#: {len(power1)}, second#: {len(power2)}")

        pass
    pass


if __name__ == '__main__':
    read_csv_2_dict()
    compare_2_csv()

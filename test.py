import xml.etree.ElementTree as ET
import os
from parse import *
import subprocess

path = "check/"
def main():
    log_file = open("log.txt", "a", encoding='utf-8')
    for file in os.listdir(path):
        root = load_mjlog(os.path.join(path, file))
        try:
            parsed = parse_mjlog_to_mjai(root)
        except Exception as e: 
            print("parse_mjlog_to_mjai failed:", file)
            print("reason: ", e)
            print("parse_mjlog_to_mjai failed:", file, file=log_file)
            print("reason: ", e, file=log_file)
            continue
        tenhou_id = file.split(".")[0].split("&")[0]
        cmd = "path/to/akochan_ui/mjai-reviewer/target/debug/mjai-reviewer --no-review --tenhou-id " + tenhou_id + " --mjai-out -"
        try:
            output = subprocess.check_output(cmd.split())
            data = output.decode('utf-8').rstrip()
            if data != parsed:
                print("mjai-reviewer failed:", tenhou_id)
                print("mjai-reviewer failed:", tenhou_id, file=log_file)
                print(parsed, file=open("actual.txt", "w", encoding='utf-8'))
                print(data, file=open("expected.txt", "w", encoding='utf-8'))
                for i, j in zip(data.split("\n"), parsed.split("\n")):
                    if i != j:
                        print(i)
                        print(j)
                        print(i, tenhou_id, file=log_file)
                        print(j, tenhou_id, file=log_file)
                        assert 'kakan' in i and ('5mr' in i or '5sr' in i or '5pr' in i)
            else:
                print("success:", tenhou_id)
        except:
            print("FAILED: ", tenhou_id)
            print("FAILED: ", tenhou_id, file=log_file)
if __name__ == "__main__":
    main()
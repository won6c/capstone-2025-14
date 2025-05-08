import os
import csv
import time
from django.http import JsonResponse
from config import *
import sys
sys.path.append(CURRENT_DIR)
from LLM4Module.codeql import *

# 한 번 처리된 파일명을 저장할 집합
processed_taint_files = set()

columns = ["Name", "Description", "Severity", "Message", "Path", 
           "Start line", "Start column", "End line", "End column"]

def taint_func(request, filename):
    if request.method != "POST":
        return JsonResponse({"error": "POST 요청만 가능합니다!"}, status=405)

    input_file = f"{filename}.c"
    input_root = INPUT_ROOT
    output_dir = TAINT_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    csv_name = f"{filename}_security_extended.csv"
    csv_path = os.path.join(output_dir, csv_name)

    # 아직 한 번도 처리된 적이 없으면 항상 CodeQL 실행
    if filename not in processed_taint_files:
        taint = CodeQL(
            source_file=input_file,
            source_root=input_root,
            result_dir=output_dir
        )
        taint.run(2)
        # 분석이 끝날 때까지 잠시 대기
        time.sleep(10)
        processed_taint_files.add(filename)

    # CSV를 읽어서 JSON으로 반환
    parsed_data = []
    try:
        with open(csv_path, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == len(columns):
                    entry = {
                        columns[i]: row[i]
                        for i in range(len(columns))
                        if columns[i] != "Path"
                    }
                    parsed_data.append(entry)
    except FileNotFoundError:
        return JsonResponse(
            {"error": f"{csv_name} 파일을 찾을 수 없습니다."},
            status=500
        )

    return JsonResponse(parsed_data, safe=False)

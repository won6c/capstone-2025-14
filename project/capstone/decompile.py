import os
import subprocess
from django.http import JsonResponse
from django.conf import settings

def decompile(request):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES["file"]
        uploads_dir = os.path.join(settings.MEDIA_ROOT,"uploads")
        file_path = os.path.join(uploads_dir, uploaded_file.name)

        # media/uploads 폴더 생성
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir,exist_ok=True)
            os.makedirs(os.path.join(settings.MEDIA_ROOT,"downloads"),exist_ok=True)

        # 업로드된 파일 저장
        with open(file_path, "wb+") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        try:
            decompiled_code = run_decompiler(file_path)
            print(f"decompiled_code:\n{decompiled_code}")
            return JsonResponse({
                "decompiledCode": decompiled_code,
                "downloadUrl": f"/api/download/{uploaded_file.name}.c"
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)

def run_decompiler(file_path):
    decompiled_output = os.path.join(settings.MEDIA_ROOT,"downloads",f"{os.path.basename(file_path)}.c")
    # 예시: bof.c 파일을 복사하여 디컴파일 결과 파일 생성
    command = f"cp /app/llm4decompile/bof.c {decompiled_output}"
    # 명령어 실행 (check=True: 실패 시 예외 발생)
    subprocess.run(command, shell=True, check=True)
    
    if os.path.exists(decompiled_output):
        with open(decompiled_output, "r") as f:
            return f.read()
    return "Failed to decompile"

import os
import io
import subprocess
from django.http import JsonResponse
from django.conf import settings
from elftools.elf.elffile import ELFFile

def is_elf(file_bytes):
    if len(file_bytes) < 4:
        return False
    return file_bytes[:4]==b"\x7fELF"

def has_symbols(file_bytes):
    stream = io.BytesIO(file_bytes)
    elffile = ELFFile(stream)
    symtab = elffile.get_section_by_name('.symtab')
    if symtab and symtab.num_symbols() > 0:
        return True
    return False

def decompile(request):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES["file"]
        # 디버깅을 위한 로깅 추가
        print(f"Received file: {uploaded_file.name}, size: {uploaded_file.size} bytes")
        
        file_bytes = uploaded_file.read()

        if not is_elf(file_bytes):
            print("Not ELF file")
            return JsonResponse({"error": "Please upload ELF file"}, status=400)

        if not has_symbols(file_bytes):
            print("No symbol table")
            return JsonResponse({"error": "Please upload file with symbol table"}, status=400)

        # 절대 경로 사용
        upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads")
        download_dir = os.path.join(settings.MEDIA_ROOT, "downloads")
        file_path = os.path.join(upload_dir, uploaded_file.name)
        
        print(f"Upload directory: {upload_dir}")
        print(f"File path: {file_path}")
        
        try:
            # media/uploads 폴더 생성
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
                print(f"Created directory: {upload_dir}")

            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
                print(f"Created directory: {download_dir}")
                
            # 업로드된 파일 저장
            with open(file_path, "wb+") as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            os.chmod(file_path,0o600)
            
            print(f"Changed file({file_path}) access permission")

#            if not is_elf(file_path):
#                print("No symbol table")
#                return JsonResponse({"error":"Please upload ELF file"},status=400)

#            if not has_symbols(file_path):
#                print("No symbol table")
#                return JsonResponse({"error":"Please upload file with symbol table"})

            print(f"File saved successfully: {file_path}")
            
            decompiled_code = run_decompiler(file_path)
            print(f"Decompilation completed, code length: {len(decompiled_code)}")
            
            return JsonResponse({
                "decompiledCode": decompiled_code,
                "downloadUrl": f"/capstone/api/download/{uploaded_file.name}.c"
            })
        except Exception as e:
            print(f"Error during decompilation: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request"}, status=400)

def run_decompiler(file_path):
    decompiled_output = f"{file_path}.c"
    decompiled_output = decompiled_output.replace("uploads","downloads")
    print(f"Decompiled output path: {decompiled_output}")
    
    # 예시 파일 경로를 요청한 경로로 변경
    example_path = "/home/user/idea101/project/capstone/llm4decompile/bof.c"
    
    # 예시 파일 존재 확인
    if not os.path.exists(example_path):
        print(f"Warning: Example file {example_path} does not exist")
        # 대체 경로 시도 (프로젝트 내부에서 상대 경로 사용)
        example_path = os.path.join(settings.BASE_DIR, "capstone", "llm4decompile", "bof.c")
        print(f"Trying alternative path: {example_path}")
        
        if not os.path.exists(example_path):
            print(f"Alternative path also does not exist")
            return "Example decompiled code (example file not found)"
    
    # 명령어 실행 (check=True: 실패 시 예외 발생)
    command = f"cp {example_path} {decompiled_output}"
    print(f"Executing command: {command}")
    
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"Command executed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Command execution failed: {str(e)}")
        return "Failed to execute decompiler command"
    
    if os.path.exists(decompiled_output):
        try:
            with open(decompiled_output, "r") as f:
                content = f.read()
                print(f"Read {len(content)} bytes from output file")
                return content
        except Exception as e:
            print(f"Error reading output file: {str(e)}")
            return f"Failed to read decompiled file: {str(e)}"
    else:
        print(f"Output file does not exist: {decompiled_output}")
    
    return "Failed to decompile"

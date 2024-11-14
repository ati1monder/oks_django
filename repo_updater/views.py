from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import subprocess

@csrf_exempt
def update_repo(request):
    if request.method == 'POST':
        # Запускаем скрипт для обновления репозитория
        subprocess.run(['/home/ubuntu/scripts/update_repo.sh'])
        return JsonResponse({'status': 'Repository updated'}, status=200)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)
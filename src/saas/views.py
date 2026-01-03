from django.shortcuts import render
from pathlib import Path

base_dir = Path(__file__).resolve().parent

def saas_home(request):
    return render(request, 'index.html')

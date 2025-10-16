from django.shortcuts import render


def index(request):
    return render(request, 'cashup/index.html', {})

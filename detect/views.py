from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from API.settings import MODELS


class PublicParameters(APIView):

    def get(self, request):
        data = {
            "pad": {
                "status": True,
                "dis": 0,
                "max": 400
            },
            "coefficient": 0.35
        }
        return Response(data, status=status.HTTP_200_OK)


class AvailableModels(APIView):

    def get(self, request):
        data = {}
        for project in MODELS:
            data[project] = MODELS[project].keys()
        return Response(data, status=status.HTTP_200_OK)

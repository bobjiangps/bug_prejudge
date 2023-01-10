from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from API.settings import MODELS
from pathlib import Path
from sights.lib.visual.pred import predict
import base64
import time


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


class Detection(APIView):

    def post(self, request):
        start = time.time()
        src_category, model_category = request.data.keys()
        img_path = Path.cwd().joinpath("static", "cache_images", f"{int(time.time())}.png")
        with open(img_path, "wb") as f:
            f.write(base64.b64decode(request.data[src_category].split(",")[1]))
        model_map = {
            "Elements": "element",
            "Icons": "icon"
        }
        results, labels, _ = predict(list(MODELS[model_map[request.data[model_category]]].values())[0], str(img_path))
        end = time.time()
        data = {
            "summary": labels,
            "detail": results,
            "duration": end-start
        }
        return Response(data, status=status.HTTP_200_OK)

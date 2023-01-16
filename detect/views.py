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
        origin_path = Path.cwd().joinpath("static", "cache_images", "origin", f"{request.META.get('uuid')}.png")
        detect_path = str(origin_path).replace("origin", "detected")
        with open(origin_path, "wb") as f:
            f.write(base64.b64decode(request.data[src_category].split(",")[1]))
        model_map = {
            "Elements": "element",
            "Icons": "icon"
        }
        results, labels, _ = predict(list(MODELS[model_map[request.data[model_category]]].values())[0], str(origin_path))
        end = time.time()
        data = {
            "summary": labels,
            "detail": results,
            "duration": end-start
        }
        print(data)
        # shutil.copy(origin_path, detect_path)
        # img_init = cv2.imread(str(origin_path))
        # cv2.imwrite(detect_path, img_init)
        cv2.imwrite(detect_path, self.draw(cv2.imread(str(origin_path)), data))
        return Response({"url": "static" + detect_path.split("static")[-1]}, status=status.HTTP_200_OK)

    @staticmethod
    def draw(im, contents):
        hexs = ("#FF3838", "#FF9D97", "#FF701F", "#FFB21D", "#CFD231", "#48F90A", "#92CC17", "#3DDB86", "#1A9334", "#00D4BB")
        colors = {}
        for seq, s in enumerate(list(contents["summary"].keys())):
            c_temp = tuple(int(hexs[seq][1 + i:1 + i + 2], 16) for i in (0, 2, 4))
            colors[s] = (c_temp[2], c_temp[1], c_temp[0])
        for item in contents["detail"]:
            tl = 3 or round(0.002 * (im.shape[0] + im.shape[1]) / 2) + 1
            c1, c2 = (int(item["COOR"][0]), int(item["COOR"][1])), (int(item["COOR"][2]), int(item["COOR"][3]))
            cv2.rectangle(im, c1, c2, colors[item["N"]], thickness=tl, lineType=cv2.LINE_AA)
            tf = max(tl - 1, 1)
            t_size = cv2.getTextSize(f"{item['N']}: {item['PR']}", 0, fontScale=tl / 3, thickness=tf)[0]
            c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
            cv2.rectangle(im, c1, c2, colors[item["N"]], -1, cv2.LINE_AA)
            cv2.putText(im, f"{item['N']}: {item['PR']}", (c1[0], c1[1] - 2), 0, tl / 3, [225, 255, 255], thickness=tf, lineType=cv2.LINE_AA)
        return im

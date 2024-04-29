import cv2
import numpy as np
import time
import paho.mqtt.client as mqtt # type: ignore
import datetime



def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")

client = mqtt.Client()
client.on_connect = on_connect
client.connect("broker.emqx.io", 1883, 60)


cap=cv2.VideoCapture('demo1.mp4')#链接摄像头时注释掉此行
#cap=cv2.VideoCapture(0)#链接摄像头时启用，usb摄像头0改为1

cap.set(3,720)
cap.set(4,480)
cap.set(5,60)
 
KNN=cv2.createBackgroundSubtractorKNN()
 
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
kernel2 = cv2.getStructuringElement(cv2.MORPH_RECT, (8,8))
cars=0

car=[]
last_car_time = time.time()
end_time = time.time()
car_count = 0

 
while True:
    ret, frame = cap.read()
    if(ret == True):     
        
        cvtc=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)#灰度化
        
        
        blur=cv2.GaussianBlur(cvtc,(3,3),8);#高斯模糊
        
        
        mask=KNN.apply(blur)#背景剪除
        cv2.imshow('KNN',mask)
        
        
        ero=cv2.erode(mask,kernel,2)
        ero2=cv2.erode(ero,kernel)#腐蚀
        
        
        dil=cv2.dilate(ero2,kernel2,2)
        dil2=cv2.dilate(dil,kernel2)#膨胀
        cv2.imshow('5',dil2)
        
        
        contour,hierarchy=cv2.findContours(dil2, 0, cv2.CHAIN_APPROX_SIMPLE)#寻找轮廓
        
        min_w=40
        min_h=40
        
        for(i,c) in enumerate(contour):
            (x,y,w,h) = cv2.boundingRect(c)#计算轮廓最小外接矩形并储存参数
            
            
            if(w<min_w or h<min_h):
                continue
            
            
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255,0,0), 1)#框出轮廓
            
            #计算矩形中心
            x1 = int(w/2)
            y1 = int(h/2)
            cx = x + x1
            cy = y + y1
            cpoint = (cx,cy)
            car.append(cpoint)
            cv2.circle(frame, (cpoint), 2, (0,0,255), -1)#画出轮廓中心
            
            
            
            for (x, y) in car:#判断轮廓中点是否在检测线内，若不在，则删除该坐标，若在，则计数加一
                if( (y > 240 - 6) and (y < 240 + 6) ):
                    cars +=1
                    car_count +=1
                    print("cars:" + str(cars))
                    client.publish('raspberry/topicnum', payload="cars" + str(cars), qos=0, retain=False)
                    car.remove((x , y ))
            if time.time() - last_car_time > 20:#车流量计数部分
                car_count = 0
                last_car_time = time.time()
            if car_count>2:
                num = "MORE"
                print("data:" + str(car_count) + " MORE")
                client.publish('raspberry/topicnum', payload=str(car_count) + "--MORE", qos=0, retain=False)
            if car_count<=2:
                num = "LESS"
                print("data:" + str(car_count) + " LESS")
                client.publish('raspberry/topicnum', payload=str(car_count) + "--LESS", qos=0, retain=False)
            if time.time() - end_time > 20:
                end_car_time = time.time()
            cv2.putText(frame, "Car:" + str(cars) + "Data" + str(car_count) +"/8s" + num, (0, 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2)#在屏幕上显示经过的车的数量
            cv2.line(frame, (0, 240), (720, 240), (0, 255, 0), 2)
        cv2.imshow('video', frame)
    key = cv2.waitKey(1)
    if(key == 27):
        break
 
cap.release()
cv2.destroyAllWindows()
 

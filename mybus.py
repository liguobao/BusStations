import requests
from bs4 import BeautifulSoup
import csv
import json

mianyang_bus = "http://mianyang.8684.cn/"
headers = {
    'connection': "keep-alive",
    'cache-control': "no-cache",
    'upgrade-insecure-requests': "1",
    'user-agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36",
    'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    'accept-encoding': "gzip, deflate",
    'accept-language': "zh-CN,zh;q=0.9,en;q=0.8,da;q=0.7"
}
response = requests.request("GET", mianyang_bus, headers=headers)
htmlSoup = BeautifulSoup(response.text, "html.parser")
# class 为bus_kt_r1 的第一个元素,就是那个数字分类:1,2,3,4
bus_kt_r1 = htmlSoup.find(
    attrs={"class": "bus_kt_r1"})
bus_url_list = []
if bus_kt_r1:
    # 获取这个元素下面所有的a标签
    for a in bus_kt_r1.find_all('a'):
        category_url = "http://mianyang.8684.cn" + a["href"]
        response = requests.request("GET", category_url, headers=headers)
        stie_list = BeautifulSoup(response.text, "html.parser").find(
            attrs={"class": "stie_list"})
        if stie_list is None:
            continue
        for bus in stie_list.find_all("a"):
            bus_url_list.append("http://mianyang.8684.cn"+bus["href"])
bus_stations = []
for bus_url in bus_url_list:
    response = requests.request("GET", bus_url, headers=headers)
    htmlSoup = BeautifulSoup(response.text, "html.parser")
    bus_line_txt = htmlSoup.find(attrs={"class": "bus_line_txt"})
    if bus_line_txt is None:
        continue
    bus_line_name = bus_line_txt.find("strong").text
    bus_site_layer = htmlSoup.find(attrs={"class": "bus_site_layer"})
    stations = []
    for bus_site in bus_site_layer.find_all("a"):
        station = {}
        station['bus_line_name'] = bus_line_name
        station['station_name'] = bus_site.text
        bus_stations.append(station)
        print(bus_line_name + "-"+bus_site.text +
              " finish,index:" + str(len(bus_stations)))
bus_station_location_list = []
for index in range(0, len(bus_stations), 10):
    stations = bus_stations[index * 10: (index + 1) * 10]
    station_url = "http://restapi.amap.com/v3/geocode/geo?key=fed53efe358677305ad9a9cad2b93b8b&city=绵阳&batch=true"
    station_name_list = [station['station_name']
                         for station in stations if station.get('station_name')]
    station_url = station_url + "&address=" + "|".join(station_name_list)
    response = requests.request("GET", station_url, headers=headers)
    result = json.loads(response.text)
    if result['info'] == 'OK' and int(result['count']) > 0:
        for geo_index in range(0, int(result['count'])):
            stations[geo_index]['location'] = result['geocodes'][geo_index]['location']
            stations[geo_index]['geo'] = str(result['geocodes'][geo_index])
            bus_station_location_list.append(stations[geo_index])
    print("finish" + "|".join(station_name_list) + "index:" + str(index))
with open('mianyang_bus.csv', 'w+', newline='') as csv_file:
    fieldnames = ['bus_line_name', 'station_name', 'location', 'geo']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(bus_station_location_list)
print(bus_station_location_list)

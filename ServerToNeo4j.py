from http.server import BaseHTTPRequestHandler, HTTPServer
from os import path
from urllib.parse import urlparse
from py2neo import Graph
import string
import time
import json
from json import JSONEncoder
import numpy

curdir = path.dirname(path.realpath(__file__))
sep = '/'

# MIME-TYPE
mimedic = [
    ('.html', 'text/html'),
    ('.htm', 'text/html'),
    ('.js', 'application/javascript'),
    ('.css', 'text/css'),
    ('.json', 'application/json'),
    ('.png', 'image/png'),
    ('.jpg', 'image/jpeg'),
    ('.gif', 'image/gif'),
    ('.txt', 'text/plain'),
    ('.avi', 'video/x-msvideo'),
]




class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, numpy.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):

    graph = Graph('bolt://localhost:7687', username='neo4j', password='casia@1234')

    # GET
    def do_GET(self):
        sendReply = False
        querypath = urlparse(self.path)
        filepath, query = querypath.path, querypath.query

        if filepath.endswith('/'):
            filepath += 'index.html'
        filename, fileext = path.splitext(filepath)
        for e in mimedic:
            if e[0] == fileext:
                mimetype = e[1]
                sendReply = True

        if sendReply == True:
            try:
                with open(path.realpath(curdir + sep + filepath), 'rb') as f:
                    content = f.read()
                    self.send_response(200)
                    self.send_header('Content-type', mimetype)
                    self.end_headers()
                    self.wfile.write(content)  # 封装需要响应的内容信息
            except IOError:
                self.send_error(404, 'File Not Found: %s' % self.path)

    def do_POST(self):
        # print(self.headers)
        # print(self.command)
        req_datas = self.rfile.read(int(self.headers['content-length']))  # 重点在此步!

        # print("receive DATA:", req_datas.decode())

        # print(type(req_datas.decode()))

        str = req_datas.decode()
        reDict = json.loads(str)

        # print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

        # b = '%d' % int(time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())))
        # print(type(b))

        trackletID = 'cam'+reDict['camID'] + "_" + '%d' % reDict['tid'] + "_" + time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        # print(trackletID)
        # print(type(trackletID))

        cql = 'CREATE (n:Person16Ceng { ' \
            'person_id:' + '%d' % reDict['person_id'] + ' , ' \
            'trackletID:"' + trackletID + '" , ' \
            'startTime:"' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())) + '" , ' \
            'time:' + '%d' % int(time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))) + ' , ' \
            'camID:"' + reDict['camID'] + '" , ' \
            'genderMale:' + '%f' % reDict['male'] + ' , ' \
            'genderFemale:' + '%f' % reDict['female'] + ' , ' \
            'ageSixteen:' + '%f' % reDict['age16less'] + ' , ' \
            'ageThirty:' + '%f' % reDict['age17_30'] + ' , ' \
            'ageFortyFive:' + '%f' % reDict['age31_45'] + ' , ' \
            'ageSixty:' + '%f' % reDict['age46_60'] + ' , ' \
            'camIP:"' + reDict['camIP'] + '" , ' \
            'person_bbox:"' + reDict['person_bbox'] + '" , ' \
            'selected_idx:"' + reDict['selected_idx'] + '" , ' \
            'face:"' + reDict['face'] + '" , ' \
            'save_flag:' + '%d' % reDict['save_flag'] + ' , ' \
            'path:"' + reDict['imgPath'] + '"});'


        # 'camID:' + '%d' % reDict['camID'] + ' , ' \

        # 'reid_feats:"' + reDict['reid_feats'] + '" , ' \

        # print(cql)
        self.graph.run(cql)


        # 创建日期节点
        cqlDay = 'MATCH(n: Day:Person16Ceng{day:' + '%d' % int(
            time.strftime('%Y%m%d', time.localtime(time.time()))) + '}) RETURN n LIMIT 25'
        dayNode = self.graph.run(cqlDay).data()
        # print(dayNode.__len__())
        if dayNode.__len__() == 0:
            self.graph.run('merge (n:Day:Person16Ceng{day:' + '%d' % int(
                time.strftime('%Y%m%d', time.localtime(time.time()))) + '})')
        else:
            for i in dayNode:
                print(i)

        # 创建关系
        print(int(time.strftime('%Y%m%d', time.localtime(time.time()))))
        # print("****************")
        relationCql = 'match (a:Day:Person16Ceng{day:' + '%d' % int(time.strftime('%Y%m%d', time.localtime(time.time()))) + \
                      '}), (b:Person16Ceng{trackletID:"' + trackletID + '"}) merge (a)-[r:INCLUDES_PERSON{DataType:"Person16Ceng"}]->(b) return r'
        print(relationCql)

        g = self.graph.run(relationCql).data()


        print("****************")
        data = {
            'result_code': '2',
            'result_desc': 'Success',
            'timestamp': '',
            'data': {'message_id': '25d55ad283aa400af464c76d713c07ad'}
        }
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))


def run():
    port = 8000
    print('starting server, port', port)
    server_address = ('172.18.33.3', port)
    httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)
    print('running server...')
    httpd.serve_forever()


if __name__ == '__main__':
    run()

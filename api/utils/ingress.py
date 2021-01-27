#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : ingress.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/23
# @Desc  :
'''
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: h5
  namespace: h5
  annotations:
    # 请求头中满足正则匹配foo=bar的请求才会被路由到新版本服务new-nginx中
    nginx.ingress.kubernetes.io/service-match: 'preview-v3: header("ab", "test")'
    nginx.ingress.kubernetes.io/service-weight: ''
  generation: 1

spec:
  rules:
    - host: h5.pigs.com
      http:
        paths:
          # 老版本服务
          - backend:
              serviceName: v3
              servicePort: 80
            path: /
          # 新版本服务
          - backend:
              serviceName: preview-v3
              servicePort: 80
            path: /
  tls:
  - hosts:
    - h5.pigs.com
    secretName: h5.pigs.com
status:
  loadBalancer:
    ingress:
    - ip: 172.18.1.135


'''
from kubernetes import client, config
import re

config.load_kube_config()
api_instance = client.ExtensionsV1beta1Api()


def get_namespaces_ingress(name, namespace):
    """
    params: name str | name of the Ingress
    params: namespace str | object name and auth scope, such as for teams and projects
    """
    pretty = 'pretty_example'  # str | If 'true', then the output is pretty printed. (optional)
    api_response = api_instance.read_namespaced_ingress(name, namespace, pretty=pretty, )
    ingress_re = api_response.metadata.annotations['nginx.ingress.kubernetes.io/service-match']
    # pattern = re.compile(u'(header?P<key>\"\w+\"), (?P<value>\"\w+\")')
    pattern = re.compile(u'(header\("\w+\"), (\"\w+\"\))')
    cookie_pattern = re.compile(u'(cookie\("\w+\"), (\"\w+\"\))')

    # result = pattern.search(ingress_re).group('key')
    key = 'HELLO'
    value = 'GO'
    new_ingress_header = re.sub(pattern, r'header("%s", "%s")' % (key, value), ingress_re)
    new_ingress_cookie = re.sub(cookie_pattern, r'cookie("%s", "%s")' % (key, value), ingress_re)
    print(new_ingress_header)
    print(new_ingress_cookie)

    # ss = new_ingress_header.strip().split(':')
    # print(ss)
    api_response.metadata.annotations['nginx.ingress.kubernetes.io/service-match'] = new_ingress_header
    # print(ingress_re)
    # print(api_response.metadata.annotations['nginx.ingress.kubernetes.io/service-match'])

get_namespaces_ingress(name='h5', namespace='h5')
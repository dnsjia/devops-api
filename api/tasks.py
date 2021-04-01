#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/11/4 16:52
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: tasks.py

"""

from __future__ import absolute_import
from celery import shared_task
from django.db.models import Q
from api.models import DeployStatusChart
import datetime as dt
import json
import traceback
import requests
from api.utils.dingtalk_notice import DingTalkSendMsg
from django.core.mail import EmailMultiAlternatives
from api.utils.check_jenkins import JenkinsStatus
from django_redis import get_redis_connection
from jenkinsapi.jenkins import Jenkins
from decouple import config
from api.models import SyncJobHistory, DeployTask
import time
import logging

from auto_case.testcase import RunnerTestCase

logger = logging.getLogger('default')


@shared_task
def dashboard_deploy_chart_count():
    """
    部署状态结转
    :return:
    """
    today = dt.date.today()
    week_ago = today - dt.timedelta(days=1)
    str_today = str(today)
    try:
        success_count = DeployTask.objects.filter(
            Q(created_time__startswith=str_today, status=4)).count()

        if success_count == 0:
            DeployStatusChart.objects.update_or_create(defaults={'count': 0}, days=str_today, deploy_status='部署成功')

        else:
            DeployStatusChart.objects.update_or_create(defaults={'count': success_count}, days=str_today,deploy_status='部署成功')

    except BaseException as e:
        logger.error('部署成功状态统计结转失败, 异常原因: %s' % str(traceback.format_exc()), e)

    try:
        failed_count = DeployTask.objects.filter(
            Q(created_time__startswith=str_today, status=5)).count()
        if failed_count == 0:
            DeployStatusChart.objects.update_or_create(defaults={'count': 0}, days=str_today, deploy_status='部署失败')
        else:
            DeployStatusChart.objects.update_or_create(defaults={'count': failed_count}, days=str_today,deploy_status='部署失败')

    except BaseException as e:
        logger.error('部署成功状态统计结转失败, 异常原因: %s' % str(traceback.format_exc()), e)

alarm_user = '1508870xxxx,1508870xxxx'
notice_url = 'https://oapi.dingtalk.com/robot/send?access_token=xxxxxxxxxxxxxxxxxx'
cache_redis = get_redis_connection('default')


@shared_task
def send_deploy_email(email, name, title, msg, msg_en, url, subject='小飞猪运维平台-您有一条工单待审批！'):
    """
    发送邮件验证码
    :param email:  邮箱
    :param get_random_code: 验证码
    :return:
    """
    text_content = '''测试'''

    css = '''<style type="text/css">
		p{
			margin:10px 0;
			padding:0;
		}
		table{
			border-collapse:collapse;
		}
		h1,h2,h3,h4,h5,h6{
			display:block;
			margin:0;
			padding:0;
		}
		img,a img{
			border:0;
			height:auto;
			outline:none;
			text-decoration:none;
		}
		body,#bodyTable,#bodyCell{
			height:100%;
			margin:0;
			padding:0;
			width:100%;
		}
		.mcnPreviewText{
			display:none !important;
		}
		#outlook a{
			padding:0;
		}
		img{
			-ms-interpolation-mode:bicubic;
		}
		table{
			mso-table-lspace:0pt;
			mso-table-rspace:0pt;
		}
		.ReadMsgBody{
			width:100%;
		}
		.ExternalClass{
			width:100%;
		}
		p,a,li,td,blockquote{
			mso-line-height-rule:exactly;
		}
		a[href^=tel],a[href^=sms]{
			color:inherit;
			cursor:default;
			text-decoration:none;
		}
		p,a,li,td,body,table,blockquote{
			-ms-text-size-adjust:100%;
			-webkit-text-size-adjust:100%;
		}
		.ExternalClass,.ExternalClass p,.ExternalClass td,.ExternalClass div,.ExternalClass span,.ExternalClass font{
			line-height:100%;
		}
		a[x-apple-data-detectors]{
			color:inherit !important;
			text-decoration:none !important;
			font-size:inherit !important;
			font-family:inherit !important;
			font-weight:inherit !important;
			line-height:inherit !important;
		}
		.templateContainer{
			max-width:600px !important;
		}
		a.mcnButton{
			display:block;
		}
		.mcnImage,.mcnRetinaImage{
			vertical-align:bottom;
		}
		.mcnTextContent{
			word-break:break-word;
		}
		.mcnTextContent img{
			height:auto !important;
		}
		.mcnDividerBlock{
			table-layout:fixed !important;
		}
		h1{
			color:#222222;
			font-family:Helvetica;
			font-size:40px;
			font-style:normal;
			font-weight:bold;
			line-height:150%;
			letter-spacing:normal;
			text-align:center;
		}
		h2{
			color:#222222;
			font-family:Helvetica;
			font-size:34px;
			font-style:normal;
			font-weight:bold;
			line-height:150%;
			letter-spacing:normal;
			text-align:left;
		}
		h3{
			color:#444444;
			font-family:Helvetica;
			font-size:22px;
			font-style:normal;
			font-weight:bold;
			line-height:150%;
			letter-spacing:normal;
			text-align:left;
		}
		h4{
			color:#999999;
			font-family:Georgia;
			font-size:20px;
			font-style:italic;
			font-weight:normal;
			line-height:125%;
			letter-spacing:normal;
			text-align:left;
		}
		#templateHeader{
			background-color:#F2F2F2;
			background-image:none;
			background-repeat:no-repeat;
			background-position:center;
			background-size:cover;
			border-top:0;
			border-bottom:0;
			padding-top:36px;
			padding-bottom:0;
		}
		.headerContainer{
			background-color:#FFFFFF;
			background-image:none;
			background-repeat:no-repeat;
			background-position:center;
			background-size:cover;
			border-top:0;
			border-bottom:0;
			padding-top:45px;
			padding-bottom:45px;
		}
		.headerContainer .mcnTextContent,.headerContainer .mcnTextContent p{
			color:#808080;
			font-family:Helvetica;
			font-size:16px;
			line-height:150%;
			text-align:left;
		}
		.headerContainer .mcnTextContent a,.headerContainer .mcnTextContent p a{
			color:#007E9E;
			font-weight:normal;
			text-decoration:underline;
		}
		#templateBody{
			background-color:#F2F2F2;
			background-image:none;
			background-repeat:no-repeat;
			background-position:center;
			background-size:cover;
			border-top:0;
			border-bottom:0;
			padding-top:0;
			padding-bottom:0;
		}
		.bodyContainer{
			background-color:#FFFFFF;
			background-image:none;
			background-repeat:no-repeat;
			background-position:center;
			background-size:cover;
			border-top:0;
			border-bottom:0;
			padding-top:0;
			padding-bottom:45px;
		}
		.bodyContainer .mcnTextContent,.bodyContainer .mcnTextContent p{
			color:#808080;
			font-family:Helvetica;
			font-size:16px;
			line-height:150%;
			text-align:left;
		}
		.bodyContainer .mcnTextContent a,.bodyContainer .mcnTextContent p a{
			color:#007E9E;
			font-weight:normal;
			text-decoration:underline;
		}
		#templateFooter{
			background-color:#F2F2F2;
			background-image:none;
			background-repeat:no-repeat;
			background-position:center;
			background-size:cover;
			border-top:0;
			border-bottom:0;
			padding-top:0;
			padding-bottom:36px;
		}
		.footerContainer{
			background-color:#333333;
			background-image:none;
			background-repeat:no-repeat;
			background-position:center;
			background-size:cover;
			border-top:0;
			border-bottom:0;
			padding-top:45px;
			padding-bottom:45px;
		}
		.footerContainer .mcnTextContent,.footerContainer .mcnTextContent p{
			color:#FFFFFF;
			font-family:Helvetica;
			font-size:12px;
			line-height:150%;
			text-align:center;
		}
		.footerContainer .mcnTextContent a,.footerContainer .mcnTextContent p a{
			color:#FFFFFF;
			font-weight:normal;
			text-decoration:underline;
		}
	@media only screen and (min-width:768px){
		.templateContainer{
			width:600px !important;
		}

}	@media only screen and (max-width: 480px){
		body,table,td,p,a,li,blockquote{
			-webkit-text-size-adjust:none !important;
		}

}	@media only screen and (max-width: 480px){
		body{
			width:100% !important;
			min-width:100% !important;
		}

}	@media only screen and (max-width: 480px){
		.mcnRetinaImage{
			max-width:100% !important;
		}

}	@media only screen and (max-width: 480px){
		.mcnImage{
			width:100% !important;
		}

}	@media only screen and (max-width: 480px){
		.mcnCartContainer,.mcnCaptionTopContent,.mcnRecContentContainer,.mcnCaptionBottomContent,.mcnTextContentContainer,.mcnBoxedTextContentContainer,.mcnImageGroupContentContainer,.mcnCaptionLeftTextContentContainer,.mcnCaptionRightTextContentContainer,.mcnCaptionLeftImageContentContainer,.mcnCaptionRightImageContentContainer,.mcnImageCardLeftTextContentContainer,.mcnImageCardRightTextContentContainer,.mcnImageCardLeftImageContentContainer,.mcnImageCardRightImageContentContainer{
			max-width:100% !important;
			width:100% !important;
		}

}	@media only screen and (max-width: 480px){
		.mcnBoxedTextContentContainer{
			min-width:100% !important;
		}

}	@media only screen and (max-width: 480px){
		.mcnImageGroupContent{
			padding:9px !important;
		}

}	@media only screen and (max-width: 480px){
		.mcnCaptionLeftContentOuter .mcnTextContent,.mcnCaptionRightContentOuter .mcnTextContent{
			padding-top:9px !important;
		}

}	@media only screen and (max-width: 480px){
		.mcnImageCardTopImageContent,.mcnCaptionBottomContent:last-child .mcnCaptionBottomImageContent,.mcnCaptionBlockInner .mcnCaptionTopContent:last-child .mcnTextContent{
			padding-top:18px !important;
		}

}	@media only screen and (max-width: 480px){
		.mcnImageCardBottomImageContent{
			padding-bottom:9px !important;
		}

}	@media only screen and (max-width: 480px){
		.mcnImageGroupBlockInner{
			padding-top:0 !important;
			padding-bottom:0 !important;
		}

}	@media only screen and (max-width: 480px){
		.mcnImageGroupBlockOuter{
			padding-top:9px !important;
			padding-bottom:9px !important;
		}

}	@media only screen and (max-width: 480px){
		.mcnTextContent,.mcnBoxedTextContentColumn{
			padding-right:18px !important;
			padding-left:18px !important;
		}

}	@media only screen and (max-width: 480px){
		.mcnImageCardLeftImageContent,.mcnImageCardRightImageContent{
			padding-right:18px !important;
			padding-bottom:0 !important;
			padding-left:18px !important;
		}

}	@media only screen and (max-width: 480px){
		.mcpreview-image-uploader{
			display:none !important;
			width:100% !important;
		}

}	@media only screen and (max-width: 480px){
		h1{
			font-size:30px !important;
			line-height:125% !important;
		}

}	@media only screen and (max-width: 480px){
		h2{
			font-size:26px !important;
			line-height:125% !important;
		}

}	@media only screen and (max-width: 480px){
		h3{
			font-size:20px !important;
			line-height:150% !important;
		}

}	@media only screen and (max-width: 480px){
		h4{
			font-size:18px !important;
			line-height:150% !important;
		}

}	@media only screen and (max-width: 480px){
		.mcnBoxedTextContentContainer .mcnTextContent,.mcnBoxedTextContentContainer .mcnTextContent p{
			font-size:14px !important;
			line-height:150% !important;
		}

}	@media only screen and (max-width: 480px){
		.headerContainer .mcnTextContent,.headerContainer .mcnTextContent p{
			font-size:16px !important;
			line-height:150% !important;
		}

}	@media only screen and (max-width: 480px){
		.bodyContainer .mcnTextContent,.bodyContainer .mcnTextContent p{
			font-size:16px !important;
			line-height:150% !important;
		}

}	@media only screen and (max-width: 480px){
		.footerContainer .mcnTextContent,.footerContainer .mcnTextContent p{
			font-size:14px !important;
			line-height:150% !important;
		}

}</style>
'''
    html_content = '''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<!doctype html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
	<head>
    <!-- NAME: GDPR SUBSCRIBER ALERT -->
    <!--[if gte mso 15]>
    <xml>
        <o:OfficeDocumentSettings>
        <o:AllowPNG/>
        <o:PixelsPerInch>96</o:PixelsPerInch>
        </o:OfficeDocumentSettings>
    </xml>
    <![endif]-->
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>*|MC:SUBJECT|*</title>
        {css}
</head>
    <body>
<!--*|IF:MC_PREVIEW_TEXT|*-->
<!--[if !gte mso 9]><!----><span class="mcnPreviewText" style="display:none; font-size:0px; line-height:0px; max-height:0px; max-width:0px; opacity:0; overflow:hidden; visibility:hidden; mso-hide:all;">*|MC_PREVIEW_TEXT|*</span><!--<![endif]-->
<!--*|END:IF|*-->
<center>
    <table align="center" border="0" cellpadding="0" cellspacing="0" height="100%" width="100%" id="bodyTable">
        <tr>
            <td align="center" valign="top" id="bodyCell">
                <!-- BEGIN TEMPLATE // -->
                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                    <tr>
                        <td align="center" valign="top" id="templateHeader">
                            <!--[if (gte mso 9)|(IE)]>
                            <table align="center" border="0" cellspacing="0" cellpadding="0" width="600" style="width:600px;">
                            <tr>
                            <td align="center" valign="top" width="600" style="width:600px;">
                            <![endif]-->
                            <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" class="templateContainer">
                                <tr>
                                    <td valign="top" class="headerContainer tpl-container" mc:container="header_container" mccontainer="header_container"><div mc:block="8656672" mc:blocktype="image" mcblock="8656672" mcblocktype="image" class="tpl-block"><table border="0" cellpadding="0" cellspacing="0" width="100%" class="mcnImageBlock" style="min-width:100%;">
<tbody class="mcnImageBlockOuter">
            <tr>
                <td valign="top" style="padding:9px" class="mcnImageBlockInner">
                    <table align="left" width="100%" border="0" cellpadding="0" cellspacing="0" class="mcnImageContentContainer" style="min-width:100%;">
                        <tbody><tr>
                            <td class="mcnImageContent" valign="top" style="padding-right: 9px; padding-left: 9px; padding-top: 0; padding-bottom: 0; text-align:center;">
                                        <img align="center" alt="" src="https://www.pigs.com/images/login/loginlogo.png" width="196" style="max-width:196px; padding-bottom: 0; display: inline !important; vertical-align: bottom;" class="mcnImage">
                            </td>
                        </tr>
                    </tbody></table>
                </td>
            </tr>
    </tbody>
</table></div></td>
                                </tr>
                            </table>
                            <!--[if (gte mso 9)|(IE)]>
                            </td>
                            </tr>
                            </table>
                            <![endif]-->
                        </td>
                    </tr>
                    <tr>
                        <td align="center" valign="top" id="templateBody">
                            <!--[if (gte mso 9)|(IE)]>
                            <table align="center" border="0" cellspacing="0" cellpadding="0" width="600" style="width:600px;">
                            <tr>
                            <td align="center" valign="top" width="600" style="width:600px;">
                            <![endif]-->
                            <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" class="templateContainer">
                                <tr>
                                    <td valign="top" class="bodyContainer tpl-container" mc:container="body_container" mccontainer="body_container"><div mc:block="8656676" mc:blocktype="text" mcblock="8656676" mcblocktype="text" class="tpl-block"><table border="0" cellpadding="0" cellspacing="0" width="100%" class="mcnTextBlock" style="min-width:100%;">
<tbody class="mcnTextBlockOuter">
<tr>
    <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
        <!--[if mso]>
        <table align="left" border="0" cellspacing="0" cellpadding="0" width="100%" style="width:100%;">
        <tr>
        <![endif]-->

        <!--[if mso]>
        <td valign="top" width="600" style="width:600px;">
        <![endif]-->
        <table align="left" border="0" cellpadding="0" cellspacing="0" style="max-width:100%; min-width:100%;" width="100%" class="mcnTextContentContainer">
            <tbody><tr>

                <td valign="top" class="mcnTextContent" style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px;">

                    <h3>Hello ， {name}</h3>

<p>{title}:<br>
<p>&nbsp; &nbsp; {msg}</p>

<p>&nbsp; &nbsp;{msg_en}</p>

                        </td>
                    </tr>
                </tbody></table>
				<!--[if mso]>
				</td>
				<![endif]-->

				<!--[if mso]>
				</tr>
				</table>
				<![endif]-->
            </td>
        </tr>
    </tbody>
</table></div><div mc:block="8656680" mc:blocktype="divider" mcblock="8656680" mcblocktype="divider" class="tpl-block"><table border="0" cellpadding="0" cellspacing="0" width="100%" class="mcnDividerBlock" style="min-width:100%;">
    <tbody class="mcnDividerBlockOuter">
        <tr>
            <td class="mcnDividerBlockInner" style="min-width: 100%; padding: 9px 18px 0px;">
                <table class="mcnDividerContent" border="0" cellpadding="0" cellspacing="0" width="100%" style="min-width:100%;">
                    <tbody><tr>
                        <td>
                            <span></span>
                        </td>
                    </tr>
                </tbody></table>

            </td>
        </tr>
    </tbody>
</table></div><div mc:block="8656684" mc:blocktype="button" mcblock="8656684" mcblocktype="button" class="tpl-block"><table border="0" cellpadding="0" cellspacing="0" width="100%" class="mcnButtonBlock" style="min-width:100%;">
    <tbody class="mcnButtonBlockOuter">
        <tr>
            <td style="padding-top:0; padding-right:18px; padding-bottom:18px; padding-left:18px;" valign="top" align="center" class="mcnButtonBlockInner">
                <table border="0" cellpadding="0" cellspacing="0" class="mcnButtonContentContainer" style="border-collapse: separate !important;border-radius: 3px;background-color: #00ADD8;">
                    <tbody>
                        <tr>
                            <td align="center" valign="middle" class="mcnButtonContent" style="font-family: Helvetica; font-size: 18px; padding: 18px;">
                                <a class="mcnButton " title="查看详情" href="{url}" target="_self" style="font-weight: bold;letter-spacing: -0.5px;line-height: 100%;text-align: center;text-decoration: none;color: #FFFFFF;">查看详情</a>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </td>
        </tr>
    </tbody>
</table></div></td>
                </tr>
            </table>
            <!--[if (gte mso 9)|(IE)]>
            </td>
            </tr>
            </table>
            <![endif]-->
        </td>
    </tr>
    <tr>
        <td align="center" valign="top" id="templateFooter">
            <!--[if (gte mso 9)|(IE)]>
            <table align="center" border="0" cellspacing="0" cellpadding="0" width="600" style="width:600px;">
            <tr>
            <td align="center" valign="top" width="600" style="width:600px;">
            <![endif]-->
            <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" class="templateContainer">
                <tr>
                    <td valign="top" class="footerContainer tpl-container" mc:container="footer_container" mccontainer="footer_container"><div mc:block="8656688" mc:blocktype="footer" mcblock="8656688" mcblocktype="footer" class="tpl-block"><table border="0" cellpadding="0" cellspacing="0" width="100%" class="mcnTextBlock" style="min-width:100%;">
<tbody class="mcnTextBlockOuter">
<tr>
    <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
        <!--[if mso]>
        <table align="left" border="0" cellspacing="0" cellpadding="0" width="100%" style="width:100%;">
        <tr>
        <![endif]-->

        <!--[if mso]>
        <td valign="top" width="600" style="width:600px;">
        <![endif]-->
        <table align="left" border="0" cellpadding="0" cellspacing="0" style="max-width:100%; min-width:100%;" width="100%" class="mcnTextContentContainer">
            <tbody><tr>

                <td valign="top" class="mcnTextContent" style="padding: 0px 18px 9px; font-family: Arvo, Courier, Georgia, serif; font-style: normal; font-weight: normal;">

                    <em>Copyright © 小飞猪运维平台 All rights reserved.</em>
                </td>
            </tr>
        </tbody></table>
        <!--[if mso]>
        </td>
        <![endif]-->

        <!--[if mso]>
        </tr>
        </table>
        <![endif]-->
    </td>
    </tr>
    </tbody>
</table></div></td>
                </tr>
            </table>
            <!--[if (gte mso 9)|(IE)]>
            </td>
            </tr>
            </table>
            <![endif]-->
        </td>
    </tr>
</table>
<!-- // END TEMPLATE -->
</td>
</tr>
</table>
</center>
</body>
</html>
'''

    message = EmailMultiAlternatives(subject, text_content, '运维平台<system@pigs.com>', [email])
    message.attach_alternative(html_content.format(css=css, title=title, name=name, msg=msg, msg_en=msg_en, url=url),
                               "text/html")
    message.send()

    # send_deploy_email(email)


@shared_task
def send_dingtalk_group(data="异步钉钉通知"):
    """
    工单审批/账号申请/提醒
    :param self:notice_url
    :param data:
    :return:
    """

    headers = {
        'Content-Type': 'application/json;charset=utf-8',
    }

    at_user = alarm_user.split(',')
    json_text = {
        "msgtype": "text",
        "at": {
            "atMobiles":
                at_user,
            "isAtAll": False  # 为True表示@所有人
        },
        "text": {
            "content": data
        }
    }
    try:

        rsp = requests.post(notice_url, json.dumps(json_text), headers=headers).content
        print(rsp)
    except Exception as e:
        logger.error('钉钉消息发送失败, 异常原因: %s' % str(traceback.format_exc()))
        #raise self.retry(exec=e, countdown=1)


@shared_task
def deploy_send_develop_dingtalk_group(data="异步钉钉通知", at_develop_user=None):
    """
    应用部署成功后， 给研发人发送钉钉群组通知
    :param self:notice_url
    :param data:
    :return:
    """
    develop_group_notice_url = 'https://oapi.dingtalk.com/robot/send?access_token=xxxxxxxxxxxxxxxxxxx'
    headers = {
        'Content-Type': 'application/json;charset=utf-8',
    }

    json_text = {
        "msgtype": "text",
        "at": {
            "atMobiles":
                at_develop_user,
            "isAtAll": False  # 为True表示@所有人
        },
        "text": {
            "content": data
        }
    }
    try:
        rsp = requests.post(develop_group_notice_url, json.dumps(json_text), headers=headers).content
        print(rsp)
    except Exception as e:
        logger.error('钉钉消息发送失败, 异常原因: %s' % str(traceback.format_exc()))
        #raise self.retry(exec=e, countdown=1)


@shared_task
def deploy_send_dingtalk_work_notice(data):
    print(data)
    """
    发送钉钉工作通知
    :param data: dict
    :return:
    """
    try:
        title = data['title']
        msg = data['msg']
        user_id = data['user_id']
        DingTalkSendMsg.send_msg(title, msg, user_id)
        logger.info('部署单审批工作钉钉通知发送成功, title: %s msg: %s  user_id: %s' % (title,msg,user_id))

    except BaseException as e:
        logger.error('审批工作通知发送失败, 异常原因: %s' % str(traceback.format_exc()))


@shared_task
def check_status(project_name, build_id, task_id):
    """
    轮询部署任务构建状态,返回success或fail
    :param project_name: 部署项目名称
    :param build_id: 部署任务id
    :param task_id: 上线部署单id
    :return:
    """

    deploy_status = JenkinsStatus.jenkins_task_status(project_name=project_name, build_id=int(build_id),task_id=task_id)
    return deploy_status


@shared_task
def check_trip_common_status(common_package, build_id, task_id, user_name, deploy_type, project_name):

    """
    轮询部署任务构建状态,返回success或fail
    :param common_package: 基础包名称
    :param project_name: 部署项目名称
    :param build_id: 部署任务id
    :param task_id: 上线部署单id
    :param user_name: 用户
    :param deploy_type: 部署类型
    :return:
    """

    from api.utils.jenkins_trip_common import TripCommon
    deploy_status = TripCommon.jenkins_task_status(
        common_package=common_package,
        build_id=int(build_id),
        task_id=task_id,
        user_name=user_name,
        deploy_type=deploy_type,
        project_name=project_name
    )
    return deploy_status


@shared_task
def check_rollback_status(project_name, build_id):
    """
    检查项目回滚状态
    :param project_name:
    :param build_id:
    :return:
    """
    rollback_status = JenkinsStatus.jenkins_rollback_status(project_name=project_name, build_id=int(build_id))


@shared_task
def sync_code_job_cluster(project_name, task_id):
    """
    集群机器代码同步任务, def check_status方法中判断当项目部署完成后并且是success成功状态则调用本方法
    :param project_name: 项目名称
    :param task_id: 任务编号
    :return:
    """

    sync_job_name = config('SYNC_JOB_NAME').split(',')
    server_2 = Jenkins(config('JENKINS_URL'), username=config('JENKINS_USER'), password=config('JENKINS_PASS'))

    if project_name in sync_job_name:
        time.sleep(120)
        logger.info(
            "开始同步集群代码：params={'sync_project': %s, 'code': 'class', 'slb': True, 'is_restart_tomcat': True}" % project_name)
        server_2.build_job('trip-sbox-sync', params={'sync_project': project_name, 'code': 'class', 'slb': True,
                                                     'is_restart_tomcat': True})
        build_id = JenkinsStatus.jenkins_task_id('trip-sbox-sync')
        Sync_Model = SyncJobHistory()
        Sync_Model.sync_id = build_id
        Sync_Model.sync_project = project_name
        Sync_Model.sync_code_type = 'class'
        Sync_Model.created_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        Sync_Model.build_status = 'BUILD_ING'
        Sync_Model.off_slb = True
        Sync_Model.is_restart_tomcat = True
        Sync_Model.save()
        sync_cluster_result = JenkinsStatus.jenkins_sync_status(project_name='trip-sbox-sync', build_id=build_id,
                                                                task_id=task_id)
    else:
        logger.info('任务：%s, 属于单机项目无集群机器, 跳过同步。' % project_name)


@shared_task
def rollback_sync_code_job_cluster(project_name):
    """
    集群机器代码同步任务, def check_status方法中判断当项目部署完成后并且是success成功状态则调用本方法
    :param project_name: 项目名称
    :param task_id: 任务编号
    :return:
    """

    sync_job_name = config('SYNC_JOB_NAME').split(',')
    server_2 = Jenkins(config('JENKINS_URL'), username=config('JENKINS_USER'), password=config('JENKINS_PASS'))

    if project_name in sync_job_name:
        time.sleep(120)
        logger.info("回滚-->开始同步集群代码：params={'sync_project': %s, 'code': 'class', 'slb': True, 'is_restart_tomcat': True}" % project_name)
        server_2.build_job('trip-sbox-sync', params={
            'sync_project': project_name,
            'code': 'class',
            'slb': True,
            'is_restart_tomcat': True})
        build_id = JenkinsStatus.jenkins_task_id('trip-sbox-sync')
        sync_cluster_result = JenkinsStatus.jenkins_rollback_status(project_name='trip-sbox-sync', build_id=build_id)

    else:
        logger.info('回滚任务：%s, 属于单机项目无集群机器, 跳过同步。' % project_name)


@shared_task
def run_case_test(data):
    """
    异步任务运行测试任务
    """
    RunnerTestCase('test_case', data).run_report()
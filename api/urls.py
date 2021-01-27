from django.conf.urls import url
from api.views.approval import ApprovalUserView, ApprovalListView, ApprovalAllView
from api.views.deploy import DeployView, DeployDetailView, DeployAuditLogsView, ApprovalDeployStatus, DeployCode
from api.views.deploy_chart import DashboardChart, DeployChart
from api.views.flight_order_dump import FlightOrderDumpView
from api.views.rollback import DeployRollBackView, CreateDeployBackupView
from api.views.upload import UploadView, CaseUploadView
from api.views.user import UserInfoView, CheckEmailExistView, \
    UserLoginView, SendCodeView, CheckCodeView, ResetPwdView, ChangePwdView, UserAccountView, \
    UserAccountRecordView, AccountInfoView, UserRoleView
from api.views.nginx import QueryNginxView, AddHostNginxView
from api.views.project import QueryProjectView
from api.views.dingtalk import DingConf, DingCallBack
from api.views.ticket import TicketRecordView, TicketDetailView, TicketTypelView, TicketView
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token
from api.views.gray import GrayServerView, GrayDomainView
from api.views.websocket_bak import QueryDeployLogs
from api.views.database import DatabaseView
from api.views.es_manage import ElasticSearchView
app_name = 'api'


urlpatterns = [
    url(r'websocket$', QueryDeployLogs.as_view(), name='websocket'),
    url(r'^(?P<version>[v1|v2]+)/user/login$', UserLoginView.as_view(), name='login'),
    url(r'^(?P<version>[v1|v2]+)/user/getUserInfo$', UserInfoView.as_view(), name='user_info'),
    # 更新用户角色
    url(r'^(?P<version>[v1|v2]+)/user/UserRole$', UserRoleView.as_view(), name='user_role'),
    url(r'^(?P<version>[v1|v2]+)/user/getAccountInfo$', AccountInfoView.as_view(), name='account_info'),
    # 用户申请账号列表
    url(r'^(?P<version>[v1|v2]+)/user/account$', UserAccountView.as_view(), name='account'),
    # 账号申请记录
    url(r'^(?P<version>[v1|v2]+)/user/account/record$', UserAccountRecordView.as_view(), name='account_record'),
    # 工单列表
    url(r'^(?P<version>[v1|v2]+)/ticket/record$', TicketRecordView.as_view(), name='ticket_record'),
    url(r'^(?P<version>[v1|v2]+)/ticket/detail$', TicketDetailView.as_view(), name='ticket_detail'),
    url(r'^(?P<version>[v1|v2]+)/ticket/type$', TicketTypelView.as_view(), name='ticket_type'),
    url(r'^(?P<version>[v1|v2]+)/ticket$', TicketView.as_view(), name='ticket'),

    # url(r'^(?P<version>[v1|v2]+)/user/login$', obtain_jwt_token, name='token'),
    url(r'^(?P<version>[v1|v2]+)/auth/token/refresh$', refresh_jwt_token, name='refresh_token'),
    url(r'^(?P<version>[v1|v2]+)/dingding$', DingConf.as_view(), name='ding_conf'),
    url(r'^(?P<version>[v1|v2]+)/dingding/callback$', DingCallBack.as_view(), name='ding_callback'),
    url(r'^(?P<version>[v1|v2]+)/account/checkEmailExist$', CheckEmailExistView.as_view(), name='check_email'),
    url(r'^(?P<version>[v1|v2]+)/account/sendCode$', SendCodeView.as_view(), name='send_code'),
    url(r'^(?P<version>[v1|v2]+)/account/checkCode$', CheckCodeView.as_view(), name='check_code'),
    url(r'^(?P<version>[v1|v2]+)/account/resetPwd$', ResetPwdView.as_view(), name='reset_pwd'),
    url(r'^(?P<version>[v1|v2]+)/account/changePassWord$', ChangePwdView.as_view(), name='change_pwd'),
    url(r'^(?P<version>[v1|v2]+)/nginx/query$', QueryNginxView.as_view(), name='query_nginx'),
    url(r'^(?P<version>[v1|v2]+)/nginx/host$', AddHostNginxView.as_view(), name='host_nginx'),
    # url(r'^(?P<version>[v1|v2]+)/nginx/register', ModifyNginx.as_view(), name='modify_nginx'),
    url(r'^(?P<version>[v1|v2]+)/gray/list$', GrayServerView.as_view(), name='gray'),
    url(r'^(?P<version>[v1|v2]+)/gray/domain/list$', GrayDomainView.as_view(), name='gray_domain'),
    # 项目
    url(r'^(?P<version>[v1|v2]+)/project/query$', QueryProjectView.as_view(), name='query_project'),
    url(r'^(?P<version>[v1|v2]+)/project/approvalUser$', ApprovalUserView.as_view(), name='approval_user'),
    url(r'^(?P<version>[v1|v2]+)/project/approvalList$', ApprovalListView.as_view(), name='approval_list'),
    url(r'^(?P<version>[v1|v2]+)/project/approvalAll$', ApprovalAllView.as_view(), name='approval_list'),
    url(r'^(?P<version>[v1|v2]+)/Upload$', UploadView.as_view(), name='upload'),
    url(r'^(?P<version>[v1|v2]+)/caseUpload$', CaseUploadView.as_view(), name='caseUpload'),
    url(r'^(?P<version>[v1|v2]+)/deploy$', DeployView.as_view(), name='deploy'),
    url(r'^(?P<version>[v1|v2]+)/deploy/detail$', DeployDetailView.as_view(), name='deploy_detail'),
    url(r'^(?P<version>[v1|v2]+)/deploy/audit$', DeployAuditLogsView.as_view(), name='deploy_audit_logs'),
    # 审批部署状态(同意, 拒绝)
    url(r'^(?P<version>[v1|v2]+)/deploy/approvalDeploy$', ApprovalDeployStatus.as_view(), name='update_approval_status'),
    url(r'^(?P<version>[v1|v2]+)/deploy/rollback$', DeployRollBackView.as_view(), name='deploy_rollback'),
    url(r'^(?P<version>[v1|v2]+)/deploy/backup$', CreateDeployBackupView.as_view(), name='deploy_backup'),
    # 部署代码
    url(r'^(?P<version>[v1|v2]+)/deploy/code$', DeployCode.as_view(), name='deploy_code'),
    # 仪表盘图表
    url(r'^(?P<version>[v1|v2]+)/dashboard/count$', DashboardChart.as_view(), name='dashboard_count'),
    url(r'^(?P<version>[v1|v2]+)/dashboard/deployChart$', DeployChart.as_view(), name='deploy_chart'),
    # 数据库申请、记录
    url(r'^(?P<version>[v1|v2]+)/database$', DatabaseView.as_view(), name='database'),
    # ElasticSearch
    url(r'^(?P<version>[v1|v2]+)/es/search$', ElasticSearchView.as_view(), name='search'),
    url(r'^(?P<version>[v1|v2]+)/flightOrder/download$', FlightOrderDumpView.as_view(), name='flight_order_dump'),



]
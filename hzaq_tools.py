import requests
import re
import threading

gl_timeStamp = ""
gl_cookies = {}
gl_total = 0


def show_menu():
    print("*" * 50)
    print("欢迎使用【杭州安全生产平台】V1.1")
    print("")
    print("1. 用户登陆")
    print("2. 查询课程 ")
    print("")
    print("0. 退出系统")
    print("*" * 50)


def user_login(username_str, password_str):
    """
    post登陆，并记录时间戳
    @param username_str: 用户名
    @param password_str: 密码
    @return: 返回登录状态
    """
    print("=" * 50)
    url = "http://app.hzsapw.com/v3/api/authentication/login"
    data = {"LoginMethod": 2, "LoginName": username_str, "Password": password_str, "ValidateCode": ""}
    # 提交数据，并接收响应数据,data为字典类型
    response = requests.post(url, data)
    result = response.text
    if result.find('"code":1') != -1:
        global gl_timeStamp
        global gl_cookies
        # 赋值时间戳到全局变量待使用
        gl_timeStamp = result[-12:-2]
        # 把cookies放入全局字典内待使用
        gl_cookies = {"LTSHZSAPW.AUTH": response.cookies["LTSHZSAPW.AUTH"]}
        return "用户 %s 登陆成功" % username_str
    else:
        return "用户 %s 登陆失败" % username_str


def get_user_course():
    """
获取用户购买的课程信息，并记录一些必要的参数
    @return:
    """
    print("=" * 50)
    if gl_timeStamp == "":
        print("请先登录再进行操作")
        return
    # 此处应该可以再次细分函数
    url = "http://www.hzsapw.com/v3/api/orderproduct/GetList"
    # GET方法提交数据，字典形式，此处有更专业的方法待改进
    response = requests.get(url, cookies=gl_cookies)
    # 加两行代码解决eval不能处理false的问题
    global false, null, true
    false = null = true = ''
    result = eval(response.text)
    # 取出网页返回源文本中的课程信息字典使用
    course_dict = result["result"]

    if len(course_dict) > 0:
        OrderProductId = []
        ProductGuid = []
        print("查询到 %d 门课程：" % len(course_dict))
        n = 1  # 定义一个n变量计数，作为序号
        for data in course_dict:
            print("%d.%s    总进度：%.2f%%" % (n, data["ProductName"], float(data["CompletedPeriod"]) / float(data["PassPeriod"]) * 100))
            OrderProductId.append(data["OrderProductId"])
            ProductGuid.append(data["ProductGuid"])
            n += 1  # 计数器加一
        deal_course(OrderProductId, ProductGuid)
    else:
        print("未查询到任何课程，请检查您的账户")


def deal_course(OrderProdictId, ProductGuid):
    print("=" * 50)
    # print("请输入您要进行的操作：修改[1] 删除[2] 返回上级菜单[0]")
    # 这里用户输入空白，无法转换为整数0，就会报错，因此添加此函数
    user_input = input_a('请输入您要操作的课程序号[直接回车为全部选择]：')

    if user_input <= len(OrderProdictId) and user_input > 0:  # 用户选择单一课程，则进行如下操作
        # 减去一是因为用户的输入习惯和索引不一样
        get_videoList(OrderProdictId[user_input - 1], ProductGuid[user_input - 1])
    elif user_input == 0:  # 用户选择全部课程，则进行如下操作
        get_videoList(OrderProdictId, ProductGuid)
    else:
        print("您输入的不正确，请重新输入")
        deal_course(OrderProdictId, ProductGuid)


def get_videoList(OrderProdictId, ProductGuid):
    # 需先检测传入的参数是什么类型，列表或整数
    if str(type(OrderProdictId)) == "<class 'list'>":
        i = 0
        while i < len(OrderProdictId):
            url = "http://www.hzsapw.com/v3/api/learningcatalog/getlearningproduct?productGuid=%s&orderProductId=%s" % (
                ProductGuid[i], OrderProdictId[i])
            response = requests.get(url, cookies=gl_cookies)
            # 返回一个装着所有要刷的视频ID字典
            course_dict = response.text
            # 直接传递返回全部内容,用for循环反复提交,有几个课程提交几次
            # for info in OrderProdictId:
            deal_video(course_dict, OrderProdictId[i])

            i += 1
    if str(type(OrderProdictId)) == "<class 'int'>":
        url = "http://www.hzsapw.com/v3/api/learningcatalog/getlearningproduct?productGuid=%s&orderProductId=%s" % (
            ProductGuid, OrderProdictId)
        response = requests.get(url, cookies=gl_cookies)
        # 返回一个装着所有要刷的视频ID字典
        course_dict = response.text
        # 直接传递返回全部内容
        print("课程ID： %s 开始执行" % OrderProdictId)
        deal_video(course_dict, OrderProdictId)


def video_initialization(learningCoursewareGuid, orderproductid, learningCourseCoursewareId):
    """
播放视频前初始化，并返回播放视频必须的LearningRecordId,课程结束返回-1
    @param learningCoursewareGuid:
    @param orderproductid:
    @param learningCourseCoursewareId:
    @return:
    """
    url = "http://app.hzsapw.com/v3/api/video/getdetail?learningCoursewareGuid=%s&orderproductid=%s" \
          "&learningCourseCoursewareId=%s" % (learningCoursewareGuid, orderproductid, learningCourseCoursewareId)
    # 如果未找到LearningRecordId，则可能是网络异常，重复读取
    # try 异常保护
    try:
        request = requests.get(url, cookies=gl_cookies)
        response = request.text
        if response.find("培训已结束") != -1:
            return -1
        while response.find('LearningRecordId":') == -1:
            request = requests.get(url, cookies=gl_cookies)
            response = request.text
            # print("未找到初始化LearningRecordId")
        pattern = re.compile('LearningRecordId":(.*?),"')
        result = pattern.findall(response)
        return result[0]
    except requests.exceptions.ConnectionError as a:
        pass

    # 如果只有一个匹配结果，将返回只带有一个元素的列表

    # if len(result) == 0:
    #     print("未找到初始化LearningRecordId,请联系软件管理")
    #     print(request.text)
    #     time.sleep(5)
    #     sys.exit()


def deal_video(videoList_str, OrderProdictId):
    """
循环向服务器发送视频请求，以达到刷时长的目的,参数不能传入元组
    @param videoList_str:
    @param OrderProdictId:
    """
    pattern = re.compile('LearningCourseCoursewareMappingId":(.*?),".*?LearningCoursewareGuid":"(.*?)",')
    result = pattern.findall(videoList_str)
    pattern1 = re.compile('ProductName":"(.*?)",')
    result1 = pattern1.findall(videoList_str)
    i = 0
    for info in result:
        LearningRecordId = video_initialization(info[1], OrderProdictId, info[0])
        # 由于 video_initialization 初始化函数取到空值后仍会继续执行不报错，所以这里增加判断
        while str(type(LearningRecordId)) == "<class 'NoneType'>":
            LearningRecordId = video_initialization(info[1], OrderProdictId, info[0])

        # 如果视频初始化返回-1，表示培训已结束
        if LearningRecordId == -1:
            print("当前课程培训已结束！")
            return

        url = "http://app.hzsapw.com/v3/api/video/setplayrecord?learningCoursewareGuid=%s&currentTime=1881" \
              "&learningRecordId=%s&orderProductId=%s&timestamp=%s" % (info[1], LearningRecordId,
                                                                       OrderProdictId, gl_timeStamp)
        i += 1
        print("课程：[%s] 进度：%d%%" % (result1[0], (i / len(result)) * 100))
        while True:
            thread_obj = threading.Thread(target=thread_test, args=(url,))
            thread_obj.start()

            global gl_total
            # 成功的提交次数大于250即满足条件跳出循环
            if gl_total >= 500:
                # 防止有线程继续执行,等待所有进程完成之后，清空全局变量
                thread_obj.join()
                # 清空全局变量，否则一直大于250
                gl_total = 0
                break

    print("课程：[%s] 执行完成！" % result1[0])


def thread_test(url):
    # 为了避免不必要的线程溢出，执行前先检测是否已经满足250次，满足则不执行
    global gl_total
    if gl_total >= 500:
        return
    # try语句把异常语句全部抛出而不是直接结束程序
    try:
        request = requests.get(url, cookies=gl_cookies)
        response = request.text
        if response.find("成功") != -1:
            gl_total += 1
    except requests.exceptions.RequestException as e:
        pass

    # 下面语句检测返回内容,打开会报错，因为网页返回失败，所以报错
    # print(response)


def deal_course_info_bat(text):
    """
用正则表达式处理网页返回的源文本
    @param text:课程信息源文本
    @return:返回一个列表，内有两个元组，元组索引：0为课程ID，1为课程标题，2为课程总课时，3为已学课时
    """
    # match_OBJ = re.search('OrderProductId":(.*?),"', text)
    # 创建一个pattern(模式) 对象，
    pattern = re.compile(
        r'OrderProductId":(.*?),".*?ProductName":"(.*?)",.*?PassPeriod":"(.*?)",.*?CompletedPeriod":"(.*?)",')
    result = pattern.findall(text)
    return result


def input_a(str):
    """
只允许用户输入数字内容，其他会报错
    @param str:
    @return:
    """
    text = input(str)
    if text == "":
        # 用户输入空时转换为int
        return 0
    else:
        # 其他情况全部转换为int,此处可以添加输入其他非数字返回空
        return int(text)

import hzaq_tools

while True:
    hzaq_tools.show_menu()
    action_str = input("请输入操作对应序号：")
    if action_str in ["1", "2"]:
        if action_str == "1":
            username = input("请输入账号：")
            password = input("请输入密码：")
            # 请求用户输入账号密码并输出登陆结果
            print(hzaq_tools.user_login(username, password))
        elif action_str == "2":
            hzaq_tools.get_user_course()
    elif action_str == "0":
        break
    else:
        print("=" * 50)
        print("您输入的不正确，请重新输入")

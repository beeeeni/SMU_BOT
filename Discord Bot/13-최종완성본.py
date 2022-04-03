import discord
from discord.ext import commands
import asyncio
import requests
from bs4 import BeautifulSoup
import datetime as dt
from datetime import datetime, timedelta
from urllib.request import urlopen
from urllib.error import URLError


token = 'token'

prefix = '!'
bot = commands.Bot(command_prefix = prefix)

# 봇 준비
@bot.event
async def on_ready():
    await bot.change_presence(status = discord.Status.online, activity = discord.Game("열심히 정보를 수집"))
    print("Bot is ready!")

# 원하는 시간에 강의 진도 현황과 과제 제출 현황 출력(알람 기능)
@bot.command()
async def 알람(ctx, id, pw, alarm):
    login_url = 'https://ecampus.smu.ac.kr/login/index.php'  #로그인 창 주소
    class2021_url = 'https://ecampus.smu.ac.kr/local/ubion/user/?year=2021&semester=20'  #강의 인덱스 가져오기 위한 주소
    url_lst = []
    url_lst_assign = []
    lst2 = []

    user_info = {}

    user_info['username'] = id
    user_info['password'] = pw

    try:
        html = urlopen(login_url)
    except URLError as e:
        await ctx.send('Ecampus ERROR: 이캠퍼스 페이지에 오류가 있습니다. ヽ( ຶ▮ ຶ)ﾉ!!!')
    else:
        while True:
            current_time = dt.datetime.now() + dt.timedelta(hours=9)
            time = "현재 시각: " + current_time.strftime('%Y-%m-%d %H:%M')
            hour = current_time.strftime('%H:%M')

            if alarm == hour:
                with requests.Session() as s:
                    #필요한 주소들 & selector들 미리 설정
                    request = s.post(login_url, data = user_info)
                    request3 = s.post(class2021_url, data = user_info)
                    source = request3.text
                    soup = BeautifulSoup(source,'html.parser')
                    items = soup.find_all("a", {"class", "coursefullname"})

                    #강의 제목 끌어오기
                    class_name_lst = []
                    for name in items:
                        arrange = name.get_text()
                        class_name_lst.append(arrange)     

                    #url에 있는 강의가 갖고 있는 id코드 크롤링하기
                    if (request.status_code == 200):
                        bs = BeautifulSoup(request3.text, 'html.parser')

                        lectures = bs.select('#region-main > div > div > div.course_lists > div > table > tbody > tr > td > div > a')
                    

                        class_list = []
                        for lecture in lectures:
                            class_list.append(str(lecture))
                        lst = []
                        for i in class_list:
                            index = i.find('id')
                            lst.append(int(i[index+3:index+8]))
                        count = len(lst)
                        for i in range(count):
                            url_lst_assign.append('https://ecampus.smu.ac.kr/mod/assign/index.php?id='+str(lst[i]))
                            url_lst.append('https://ecampus.smu.ac.kr/report/ubcompletion/user_progress.php?id='+str(lst[i]))


                    #강의진도현황크롤링하기
                    if (request3.status_code == 200):
                        value_lst = []
                        for i in range(count):
                            request3 = s.post(url_lst[i])
                            name_lst = []
                            rate_list = []
                            a_li = []
                            bs  = BeautifulSoup(request3.text, 'html.parser')
                            lecture_name = bs.find_all("td", {"class", "text-left"})
                            rates = bs.find_all("td", {"class", "text-center"})

                            for name in lecture_name:
                                name_lst.append(name.text.strip())
                            name_lst = name_lst[3:]

                            for rate in rates:
                                rate_list.append(str(rate.text))

                            for word in rate_list:
                                if '%' in word:         # 진도율만 뽑아내기 위해서 %가 포함된 부분만 검색
                                    a_li.append(word)
                                elif word == '-':
                                    a_li.append('0%')
                            
                            size = len(a_li)

                            i += 1
                            absent_lst = []
                            value = ''
                            for i in range(0, size - 1, 1):
                                if float(a_li[i][:-1]) < 100:
                                    string = name_lst[i] + ' -> 진도율 : ' + a_li[i]
                                    absent_lst.append(string)
                                        
                            if len(absent_lst) == 0:
                                value_lst.append("모든 강의를 100% 출석하였습니다. 아주 훌륭해요!!")
                            else:
                                for i in absent_lst:
                                    value += (i + '\n')
                                value_lst.append(value)
                                        
                    value = ''
                    embed = discord.Embed(title = '진도율 100% 미만 강의 목록(2021학년도 2학기)', description = time, color = 0xB2EBF4)
                    for i in range(count):
                        embed.add_field(name = class_name_lst[i], value = value_lst[i], inline = False)

                    #과제진도현황크롤링하기
                    if (request.status_code == 200):
                        value2_lst = []
                        for i in range(count):
                            request4 = s.post(url_lst_assign[i])

                            bs = BeautifulSoup(request4.text, 'html.parser')
                            assignment_name = bs.find_all("td", {"class", "cell c1"})
                            assignment_rates = bs.find_all("td", {"class", "cell c3"})
                            assignment_close = bs.find_all("td", {"class", "cell c2"})

                            assignment_name_lst = []
                            for name in assignment_name:
                                assignment_name_lst.append(name.text.strip())

                            assignment_rate_lst = []
                            for rate in assignment_rates:
                                assignment_rate_lst.append(rate.text.strip())

                            assignment_close_lst = []
                            for close in assignment_close:
                                assignment_close_lst.append(close.text.strip())
                            size = len(assignment_name_lst)

                            i += 1

                            absent = '미제출'
                            unsubmit_lst = []
                            value2 = ''
                                
                            for i in range(0, size):
                                if absent in assignment_rate_lst[i]:
                                    string = assignment_name_lst[i] + ' / 현황: ' + assignment_rate_lst[i] + ' / 마감일: ' + assignment_close_lst[i]
                                    unsubmit_lst.append(string)
                            
                            if absent not in assignment_rate_lst:
                                value2_lst.append('모두 제출 완료!!')
                            elif absent in assignment_rate_lst:
                                for i in unsubmit_lst:
                                    value2 += (i + '\n')
                                value2_lst.append(value2)
                    embed2 = discord.Embed(title = '미제출 현황 과제 목록(2021학년도 2학기)', description = time, color = 0xFFD8D8)
                    for i in range(count):
                        embed2.add_field(name = class_name_lst[i], value = value2_lst[i], inline = False)
                                
                    # 강의별 퀴즈 url id 추출
                    if (request.status_code == 200):
                        bs = BeautifulSoup(request3.text, 'html.parser')

                        lectures = bs.select('#region-main > div > div > div.course_lists > div > table > tbody > tr > td > div > a')

                        class_list = []
                        for lecture in lectures:
                            class_list.append(str(lecture))
                        
                        for i in range(count):
                            lst2.append('https://ecampus.smu.ac.kr/mod/quiz/index.php?id='+str(lst[i]))

                    if (request.status_code == 200):
                        value3_lst = []
                        for i in range(count):
                            request5 = s.post(lst2[i])

                            bs = BeautifulSoup(request5.text, 'html.parser')

                            quiz_name = []
                            quiz_lst = []
                            quizs = bs.select('#region-main > div > table > tbody > tr > td.cell.c1 > a')
                            
                            for quiz in quizs:
                                quiz_lst.append(str(quiz))
                                quiz_name.append(quiz.get_text())
                            
                            quiz_deadline_lst = []
                            quiz_deadlines = bs.select('#region-main > div > table > tbody > tr > td.cell.c2')
                            for d in quiz_deadlines:
                                quiz_deadline_lst.append(d.get_text())

                            quiz_id_lst = []
                            quiz_url_lst = []
                            quiz_status_lst = []
                            
                            # (int형) id만 quiz_id_lst에 담음
                            for i in quiz_lst:
                                index = i.find('id')
                                quiz_id_lst.append(int(i[index+3:index+9]))
                            #print(quiz_id_lst)

                            # 반복되는 링크와 id를 합쳐 퀴즈 url 리스트를 생성
                            cnt = len(quiz_id_lst)
                            for i in range(cnt):
                                quiz_url_lst.append('https://ecampus.smu.ac.kr/mod/quiz/view.php?id='+str(quiz_id_lst[i]))
                            #print(quiz_url_lst)
                            
                            # 퀴즈 답안 제출 확인
                            if (request5.status_code == 200):
                                for i in range(cnt):
                                    #print(quiz_name[i])
                                    request3 = s.post(quiz_url_lst[i])
                                    bs = BeautifulSoup(request3.text, 'html.parser')
                                    t = bs.select('#region-main > div > h3')
                                    # 퀴즈 미제출 시 빈 리스트가 반환되는 것을 확인 -> 빈 리스트인 경우 '미제출' 출력
                                    if t:
                                        quiz_status_lst.append('제출 완료')
                                    else:
                                        quiz_status_lst.append('미제출')
                                                
                            i += 1

                            size2 = len(quiz_name)
                            absent2 = '미제출'
                            unsubmit_lst2 = []
                            value3 = ''
                                
                            for i in range(0, size2):
                                if absent2 in quiz_status_lst[i]:
                                    string2 = quiz_name[i] + ' / 현황: ' + quiz_status_lst[i] + ' / 마감일: ' + quiz_deadline_lst[i]
                                    unsubmit_lst2.append(string2)
                            
                            if absent2 not in quiz_status_lst:
                                value3_lst.append('모두 제출 완료!!')
                            elif absent2 in quiz_status_lst:
                                for i in unsubmit_lst2:
                                    value3 += (i + '\n')
                                value3_lst.append(value3)
                    embed3 = discord.Embed(title = '미제출 퀴즈 목록(2021학년도 2학기)', description = time, color = 0xBDECB6)
                    for i in range(count):
                        embed3.add_field(name = class_name_lst[i], value = value3_lst[i], inline = False)
                    
                    await ctx.send(embed = embed)
                    await ctx.send(embed = embed2)
                    await ctx.send(embed = embed3)
            await asyncio.sleep(60)

# 확인 기능
@bot.command()
async def 확인(ctx, id, pw):
    login_url = 'https://ecampus.smu.ac.kr/login/index.php'  #로그인 창 주소
    class2021_url = 'https://ecampus.smu.ac.kr/local/ubion/user/?year=2021&semester=20'  #강의 인덱스 가져오기 위한 주소
    url_lst = []
    url_lst_assign = []
    lst2 = []

    user_info = {}

    user_info['username'] = id
    user_info['password'] = pw

    try:
        html = urlopen(login_url)
    except URLError as e:
        await ctx.send('Ecampus ERROR: 이캠퍼스 페이지에 오류가 있습니다. ヽ( ຶ▮ ຶ)ﾉ!!!')
    else:
        current_time = dt.datetime.now() + dt.timedelta(hours=9)
        time = "현재 시각: " + current_time.strftime('%Y-%m-%d %H:%M')

        with requests.Session() as s:
            #필요한 주소들 & selector들 미리 설정
            request = s.post(login_url, data = user_info)
            request3 = s.post(class2021_url, data = user_info)
            source = request3.text
            soup = BeautifulSoup(source,'html.parser')
            items = soup.find_all("a", {"class", "coursefullname"})

            #강의 제목 끌어오기
            class_name_lst = []
            for name in items:
                arrange = name.get_text()
                class_name_lst.append(arrange)     

                        #url에 있는 강의가 갖고 있는 id코드 크롤링하기
            if (request.status_code == 200):
                bs = BeautifulSoup(request3.text, 'html.parser')

                lectures = bs.select('#region-main > div > div > div.course_lists > div > table > tbody > tr > td > div > a')
                        

                class_list = []
                for lecture in lectures:
                    class_list.append(str(lecture))
                lst = []
                for i in class_list:
                    index = i.find('id')
                    lst.append(int(i[index+3:index+8]))
                count = len(lst)
                for i in range(count):
                    url_lst_assign.append('https://ecampus.smu.ac.kr/mod/assign/index.php?id='+str(lst[i]))
                    url_lst.append('https://ecampus.smu.ac.kr/report/ubcompletion/user_progress.php?id='+str(lst[i]))


            #강의진도현황크롤링하기
            if (request3.status_code == 200):
                value_lst = []
                for i in range(count):
                    request3 = s.post(url_lst[i])
                    name_lst = []
                    rate_list = []
                    a_li = []
                    bs  = BeautifulSoup(request3.text, 'html.parser')
                    lecture_name = bs.find_all("td", {"class", "text-left"})
                    rates = bs.find_all("td", {"class", "text-center"})

                    for name in lecture_name:
                        name_lst.append(name.text.strip())
                    name_lst = name_lst[3:]

                    for rate in rates:
                        rate_list.append(str(rate.text))

                    for word in rate_list:
                        if '%' in word:         # 진도율만 뽑아내기 위해서 %가 포함된 부분만 검색
                            a_li.append(word)
                        elif word == '-':
                            a_li.append('0%')
                                
                    size = len(a_li)

                    i += 1
                    absent_lst = []
                    value = ''
                    for i in range(0, size - 1, 1):
                        if float(a_li[i][:-1]) < 100:
                            string = name_lst[i] + ' -> 진도율 : ' + a_li[i]
                            absent_lst.append(string)
                                            
                    if len(absent_lst) == 0:
                        value_lst.append("모든 강의를 100% 출석하였습니다. 아주 훌륭해요!!")
                    else:
                        for i in absent_lst:
                            value += (i + '\n')
                        value_lst.append(value)
                                            
            value = ''
            embed = discord.Embed(title = '진도율 100% 미만 강의 목록(2021학년도 2학기)', description = time, color = 0xB2EBF4)
            for i in range(count):
                embed.add_field(name = class_name_lst[i], value = value_lst[i], inline = False)

            #과제진도현황크롤링하기
            if (request.status_code == 200):
                value2_lst = []
                for i in range(count):
                    request4 = s.post(url_lst_assign[i])

                    bs = BeautifulSoup(request4.text, 'html.parser')
                    assignment_name = bs.find_all("td", {"class", "cell c1"})
                    assignment_rates = bs.find_all("td", {"class", "cell c3"})
                    assignment_close = bs.find_all("td", {"class", "cell c2"})

                    assignment_name_lst = []
                    for name in assignment_name:
                        assignment_name_lst.append(name.text.strip())

                    assignment_rate_lst = []
                    for rate in assignment_rates:
                        assignment_rate_lst.append(rate.text.strip())

                    assignment_close_lst = []
                    for close in assignment_close:
                        assignment_close_lst.append(close.text.strip())
                        size = len(assignment_name_lst)

                    i += 1

                    absent = '미제출'
                    unsubmit_lst = []
                    value2 = ''
                                    
                    for i in range(0, size):
                        if absent in assignment_rate_lst[i]:
                            string = assignment_name_lst[i] + ' / 현황: ' + assignment_rate_lst[i] + ' / 마감일: ' + assignment_close_lst[i]
                            unsubmit_lst.append(string)
                                
                    if absent not in assignment_rate_lst:
                        value2_lst.append('모두 제출 완료!!')
                    elif absent in assignment_rate_lst:
                        for i in unsubmit_lst:
                            value2 += (i + '\n')
                        value2_lst.append(value2)
            embed2 = discord.Embed(title = '미제출 현황 과제 목록(2021학년도 2학기)', description = time, color = 0xFFD8D8)
            for i in range(count):
                embed2.add_field(name = class_name_lst[i], value = value2_lst[i], inline = False)
                        
            # 강의별 퀴즈 url id 추출
            if (request.status_code == 200):
                bs = BeautifulSoup(request3.text, 'html.parser')

                lectures = bs.select('#region-main > div > div > div.course_lists > div > table > tbody > tr > td > div > a')

                class_list = []
                for lecture in lectures:
                    class_list.append(str(lecture))
                            
                for i in range(count):
                    lst2.append('https://ecampus.smu.ac.kr/mod/quiz/index.php?id='+str(lst[i]))

            if (request.status_code == 200):
                value3_lst = []
                for i in range(count):
                    request5 = s.post(lst2[i])

                    bs = BeautifulSoup(request5.text, 'html.parser')

                    quiz_name = []
                    quiz_lst = []
                    quizs = bs.select('#region-main > div > table > tbody > tr > td.cell.c1 > a')
                                
                    for quiz in quizs:
                        quiz_lst.append(str(quiz))
                        quiz_name.append(quiz.get_text())
                                
                    quiz_deadline_lst = []
                    quiz_deadlines = bs.select('#region-main > div > table > tbody > tr > td.cell.c2')
                    for d in quiz_deadlines:
                        quiz_deadline_lst.append(d.get_text())

                    quiz_id_lst = []
                    quiz_url_lst = []
                    quiz_status_lst = []
                                
                    # (int형) id만 quiz_id_lst에 담음
                    for i in quiz_lst:
                        index = i.find('id')
                        quiz_id_lst.append(int(i[index+3:index+9]))
                    #print(quiz_id_lst)

                    # 반복되는 링크와 id를 합쳐 퀴즈 url 리스트를 생성
                    cnt = len(quiz_id_lst)
                    for i in range(cnt):
                        quiz_url_lst.append('https://ecampus.smu.ac.kr/mod/quiz/view.php?id='+str(quiz_id_lst[i]))
                    #print(quiz_url_lst)
                                
                    # 퀴즈 답안 제출 확인
                    if (request5.status_code == 200):
                        for i in range(cnt):
                            #print(quiz_name[i])
                            request3 = s.post(quiz_url_lst[i])
                            bs = BeautifulSoup(request3.text, 'html.parser')
                            t = bs.select('#region-main > div > h3')
                            # 퀴즈 미제출 시 빈 리스트가 반환되는 것을 확인 -> 빈 리스트인 경우 '미제출' 출력
                            if t:
                                quiz_status_lst.append('제출 완료')
                            else:
                                quiz_status_lst.append('미제출')
                                                    
                    i += 1

                    size2 = len(quiz_name)
                    absent2 = '미제출'
                    unsubmit_lst2 = []
                    value3 = ''
                                    
                    for i in range(0, size2):
                        if absent2 in quiz_status_lst[i]:
                            string2 = quiz_name[i] + ' / 현황: ' + quiz_status_lst[i] + ' / 마감일: ' + quiz_deadline_lst[i]
                            unsubmit_lst2.append(string2)
                                
                    if absent2 not in quiz_status_lst:
                        value3_lst.append('모두 제출 완료!!')
                    elif absent2 in quiz_status_lst:
                        for i in unsubmit_lst2:
                            value3 += (i + '\n')
                        value3_lst.append(value3)
            embed3 = discord.Embed(title = '미제출 퀴즈 목록(2021학년도 2학기)', description = time, color = 0xBDECB6)
            for i in range(count):
                embed3.add_field(name = class_name_lst[i], value = value3_lst[i], inline = False)
                        
            await ctx.send(embed = embed)
            await ctx.send(embed = embed2)
            await ctx.send(embed = embed3)

#명령어를 설명해주는 [[help]] 기능      
@bot.command()
async def 설명(ctx):
    
    embed4 = discord.Embed(title="명령어 설명", description="상명알리미 명령어에 대한 설명입니다 ☆～（ゝ。∂）", color = 0x403DEA)
    embed4.add_field(name="❗알람 (아이디) (비밀번호) (알람을 울릴 시간)", value = "알람을 설정해두면 매일 그 시간에 메세지를 보내드려요! (알람 시간 예시: 00:20, 09:00, 22:00 등)", inline = False)
    embed4.add_field(name="❗확인 (아이디) (비밀번호)", value="100% 미만 진도율의 강의 목록과 미제출 과제, 퀴즈 목록을 언제든 확인할 수 있어요! o(*'▽'*)/☆ﾟ’")
    embed4.set_thumbnail(url="https://w.namu.la/s/7504e0e9a2d890912ce2a3f26a02943c08b57ffabab09bafbeed76d3f4a0483710c1301b7196f0873de45a9ebd90dab177756d2b947ee11d362995dd91b33172acf30aab6b92e804528ac1dc841ce5ec1ca2c966f632688a2a90fd16e7f637eeb30f573e8d90a32726a56d3b19e254fc")

    await ctx.send(embed=embed4)
    
bot.run(token)
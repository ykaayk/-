# -*- coding:utf-8 -*-

# 实现搜索功能，预览播放mp3、（视频）和查看歌词，最后下载
# MP3：base_url = http://www.m117.com/
# MP3：base_url = http://www.wymp4.net/
# 视频：base_url = http://www.gcwdq.com/  暂不做

import wx
import time
import mp3play
import re
import os
import urllib2
import urllib
import shutil
import sys


# 界面类
class UIFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title='歌曲下载', size=(700, 500), pos=(100, 50))
        self.Cache_Path = '缓存/'  # 缓存路径
        self.Download_Path = '下载/'  # 下载路径，直接放在当前文件夹
        # panel = wx.Panel(self)
        self.all_url_songs = []  # 爬虫得到的所有url和对应歌名
        self.list_url_songs = []  # 匹配后得到所有url和对应歌名
        self.list_songs = []  # 匹配后得到的歌曲列表
        self.select_name = ''  # 输入的歌名
        self.download_url_song = []  # 选择下载/播放的url和歌曲
        self.download = Download()
        self.mp3 = None

        # 状态栏
        filemenu = wx.Menu()
        menu_about = filemenu.Append(wx.ID_ABOUT, u'关于', u'……')
        menu_exit = filemenu.Append(wx.ID_EXIT, u'退出', u'退出程序')

        # 将状态栏添加到菜单栏
        menu_bar = wx.MenuBar()
        menu_bar.Append(filemenu, u'菜单')
        self.SetMenuBar(menu_bar)

        # 将事件与状态栏链接
        self.Bind(wx.EVT_MENU, self.on_about, menu_about)
        self.Bind(wx.EVT_MENU, self.on_exit, menu_exit)

        # 添加sizer,三个按钮
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.buttons = []
        self.buttons.append(wx.Button(self, -1, '播放'))
        self.buttons.append(wx.Button(self, -1, '停止'))
        self.buttons.append(wx.Button(self, -1, '下载'))
        self.buttons.append(wx.Button(self, -1, '下载路径'))
        for i in range(4):
            self.sizer2.Add(self.buttons[i], 1, wx.EXPAND)

        # 搜索按钮和搜索栏
        # 从搜索栏中输入歌名，按下搜索开始搜索动作
        self.sizer_search = wx.BoxSizer(wx.HORIZONTAL)
        self.control_text1 = wx.TextCtrl(self, size=(600, 30))
        # 回车得到输入的歌名
        self.control_text1.Bind(wx.EVT_TEXT_ENTER, self.on_enter)

        # 搜索按钮
        self.buttons_search = wx.Button(self, -1, '搜索', size=(100, 30))
        # 搜索按钮与事件关联
        self.buttons_search.Bind(wx.EVT_BUTTON, self.on_enter)
        self.sizer_search.Add(self.control_text1, 2, wx.HORIZONTAL)
        self.sizer_search.Add(self.buttons_search, 0, wx.HORIZONTAL)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.sizer_search, 0, wx.EXPAND)
        # 定义列表和关联事件
        self.control_text2 = wx.ListBox(self, -1, (0, 1500), (700, 700), self.list_songs, wx.LB_SINGLE)

        # 事件1 双击试听，先下载再播放 (缓存路径)
        self.control_text2.Bind(wx.EVT_LEFT_DCLICK, self.on_play_song)
        # 事件2 点击按钮self.buttons[0]试听，同1
        self.buttons[0].Bind(wx.EVT_BUTTON, self.on_play_song)
        # 事件3 点击按钮self.buttons[1]暂停
        self.buttons[1].Bind(wx.EVT_BUTTON, self.on_stop_play_song)
        # 事件4 点击按钮self.buttons[2]下载
        self.buttons[2].Bind(wx.EVT_BUTTON, self.on_start_download)
        # 事件5 点击按钮self.buttons[3]显示下载路径
        self.buttons[3].Bind(wx.EVT_BUTTON, self.on_download)
        # 根据list_songs生成列表框
        self.sizer.Add(self.control_text2, 5, wx.EXPAND)
        self.sizer.Add(self.sizer2, 0, wx.EXPAND)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

        self.Show(True)
        pass

    # OnAbout事件
    def on_about(self, e):
        # 创建对话框
        dlg = wx.MessageDialog(self, '本下载器全部素材来自互联网。\n    如有侵权，你来打我啊！', '关于下载器')
        dlg.ShowModal()  # 打开对话框
        dlg.Destroy()

    # OnDownload事件
    def on_download(self, event):
        # 创建对话框
        dlg = wx.MessageDialog(self, '所有歌曲均下载到文件夹 ‘下载’ 中!')
        dlg.ShowModal()
        dlg.Destroy()

    # OnExit事件
    def on_exit(self, e):
        self.Close(True)

    # 播放事件
    def on_play_song(self, event):
        self.on_stop_play_song
        # 每次打开歌曲前先将下载url清空
        self.download_url_song = []
        # 得到选中歌曲在list_songs中的下标
        a = self.control_text2.GetSelection()
        if a != -1:
            file_name = self.list_url_songs[a][1]+'.mp3'
            self.download_url_song.append(self.list_url_songs[a])
            # 先判断歌曲是否缓存
            if os.path.exists(self.Download_Path+file_name.decode('utf-8')) or os.path.exists(self.Cache_Path+file_name.decode('utf-8')):
                # 有缓存则直接播放
                if os.path.exists(self.Cache_Path+file_name.decode('utf-8')):
                    self.play_song(self.Cache_Path, self.download_url_song[0][1])
                else:
                    self.play_song(self.Download_Path, self.download_url_song[0][1])
            else:
                # print '没缓存'
                # 没有缓存则先缓存/下载，再播放
                # 根据下标得到url和歌名
                self.start_download(self.Cache_Path)
                self.play_song(self.Cache_Path, self.download_url_song[0][1])
        else:
            event.Skip()
#
#    # 音量+按钮
#    def volume_up(self):
#        pass
#
#    # 音量-按钮
#    def volume_down(self):
#        pass

    # OnEnter事件
    def on_enter(self, event):
        self.select_name = self.control_text1.GetValue().encode('utf-8')
        # print self.select_name
        # print type(self.select_name)
        if self.select_name:
            self.find_the_song()  # 匹配歌名
            self.control_text2.Set(self.list_songs)  # 在列表框中显示匹配歌单
            event.Skip()

    # 根据歌名匹配
    def find_the_song(self):
        # 每次匹配之前先将列表清空
        self.list_songs = []
        self.list_url_songs = []
        for i in self.all_url_songs:
            # print self.select_name, type(self.select_name)
            # print i[1],type(i[1])
            if self.select_name in i[1]:
                self.list_url_songs.append(i)
                # print self.list_songs
        if len(self.list_url_songs) == 0:
            self.list_url_songs.append(('', '没有找到相匹配的歌曲'))

        # 将匹配到的歌名反馈给列表list_songs，最终在列表中显示
        for l in self.list_url_songs:
            self.list_songs.append(l[1])

    # 下载选择歌曲事件
    def on_start_download(self, event):
        # 每次打开歌曲前先将下载url清空
        self.download_url_song = []
        # 得到选中歌曲在list_songs中的下标
        a = self.control_text2.GetSelection()
        if a != -1:
            self.download_url_song.append(self.list_url_songs[a])
            file_name = self.download_url_song[0][1]+'.mp3'
            if os.path.exists(self.Download_Path+file_name.decode('utf-8')):
                # 如果有下载过则不下载，直接跳过
                event.Skip()
            elif os.path.exists(self.Cache_Path+file_name.decode('utf-8')):
                # 如果在缓冲目录则复制到下载目录
                shutil.copyfile(self.Cache_Path+file_name.decode('utf-8'), self.Download_Path+file_name.decode('utf-8'))
                event.Skip()
            else:
                # 根据下标得到url和歌名
                # print '根据下标得到URL和歌名'
                # print self.list_url_songs[a]
                self.start_download(self.Download_Path)
                event.Skip()
        else:
            event.Skip()

    # 下载选中歌曲
    def start_download(self, path):
        if self.download_url_song:
            self.download.start_download(self.download_url_song[0][0], path, self.download_url_song[0][1])
        else:
            pass

    # 播放歌曲
    def play_song(self, path, name):
        if name:
            filename = path+name+'.mp3'
            self.mp3 = mp3play.load(filename.decode('utf-8').encode('gbk'))
            self.mp3.play()
        else:
            pass

    # 停止播放歌曲
    def on_stop_play_song(self, event):
        if self.mp3:
            self.mp3.stop()
            self.mp3 = None
            event.Skip()
        else:
            pass


# 下载歌曲类
class Download(object):
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)'}

    # 获取url代码，提取最终下载链接download_url,下载
    def start_download(self, url, path, name):
        code = self.get_code(url)
        # print type(code)
        # print code
        pattern_1 = re.compile(r'<div class="down"><a class="jisudown" target="_blank" alt=".*?" href="(.*?)">')
        # print re.findall(pattern_1, code)
        before_download_url = 'http://www.m117.com'+re.findall(pattern_1, code)[0]
        # print before_download_url, '1111111111111'
        pattern_2 = re.compile(r'迅雷下载</a><a href="(.*?)" class="bendixza" id="downUrl"">本地下载</a></div>')
        before_download_url_code = self.get_code(before_download_url)
        download_url_name = []  # 下载的url和歌名
        download_url_name.append((re.findall(pattern_2, before_download_url_code))[0])
        download_url_name.append(name.decode('utf-8'))

        # 下载歌曲
        urllib.urlretrieve(download_url_name[0],  path+download_url_name[1] + '.mp3')

    # 获取url代码
    def get_code(self, url):
        request = urllib2.Request(url, headers=self.headers)
        response = urllib2.urlopen(request)
        return response.read()


# GCW爬虫类
class GCW(object):

    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)'}
        self.UI = None
        self.Base_Url_1 = 'http://www.m117.com'  # 源网站1
        self.items_1 = []  # 一级url和歌名
        self.items_2 = []  # 二级url和歌名

    def start(self):
        # 开始之前,判断是否需要初始化，无需初始则从文件中读取url_name数据剔除头两项之后传给items_2；初始之后直接使用items_2
        a = self.before()  # 判断的同时进行初始化
        if a == 'no_need':
            # 无需初始则从文件中读取url_name数据剔除头两项之后,传给items_2
            self.du_qu_shuju()  # 读取数据,剔除日期,传给items_2

        # 建立GUI
        app = wx.App()
        self.UI = UIFrame()
        self.UI.all_url_songs = self.items_2[:]
        self.UI.Show()
        app.MainLoop()

    # 是否需要初始化
    def before(self):
        if not os.path.exists('url_name.txt'):
            open_file = open('url_name.txt', 'w')
            open_file.close()
        # 读取url_name.txt文件
        read_file = open('url_name.txt', 'r')

        # 获取当前年和份月份
        time_now = time.localtime()
        year = time_now[0]
        month = time_now[1]

        a = read_file.readlines()
        read_file.close()
        # 文件为空则初始化
        if len(a) <= 10:
            # print len(a)
            self.chu_shi_hua(year, month)
        # 时间差超过一个月则初始化
        elif str(year) != a[0].strip() or str(month) != a[1].strip():
            self.chu_shi_hua(year, month)
        # 文件即不为空、时间不超过一个月，则无需初始化
        else:
            return 'no_need'

    # 初始化：得到url和歌名的列表，items_2
    def chu_shi_hua(self, year, month):
        while 1:
            self.get_url_name_1()
            self.get_url_name_2()
            # 将时间和items_2写入文件
            write_file = open('url_name.txt', 'w')
            write_file.write(str(year) + '\n')
            write_file.write(str(month) + '\n')
            for i in self.items_2:
                write_file.write(i[0] + '\n' + i[1] + '\n')
            write_file.close()
            if len(self.items_2)>= 10:
                break
            else:
                print u'初始失败，请等待重试！'
                time.sleep(2)

    # 爬虫部分
    def get_url_code(self, base_url):
        request = urllib2.Request(base_url, headers=self.headers)
        response = urllib2.urlopen(request)
        # print response.read()
        return response.read()

    # 收集所有一级url和对应的歌名，并放入items_1
    def get_url_name_1(self):
        url_code_1 = self.get_url_code(self.Base_Url_1+'/wuqu/')
        a_code = url_code_1
        pattern = re.compile(r'<a target="_blank" href="(.*?)".*?>(.*?)</a>')
        items_no = re.findall(pattern, a_code)
        for i in items_no:
            a = (self.Base_Url_1+i[0], i[1])
            self.items_1.append(a)

    # 再爬取二级歌曲名和对应网址，并放入items_2
    def get_url_name_2(self):
        url_2 = []
        # print 'here'
        # 取得一级歌名对应的url
        print u'初始化中，请稍后.....'
        for url in self.items_1:
            time.sleep(0.1)
            # print url
            url_2.append(self.get_url_code(url[0]))
        # 一级歌名对应的url寻得code，正则表达式，得到url和二级歌名，存入items_2等待匹配
        pattern = re.compile(r'<h2 class="r"><span>1.</span> <a class="l" href="(.*?)" target="_blank">(.*?)下载</a></h2>')
        m = 0
        for i in url_2:
            time.sleep(0.1)
            print u'抓取第', m, u'项中...'
            items_no = re.findall(pattern, i)
            for n in items_no:
                a = (self.Base_Url_1+n[0], n[1])
                self.items_2.append(a)
            print u'抓取完毕...\n'
            m += 1

    def du_qu_shuju(self):
        open_file = open('url_name.txt', 'r')
        a = open_file.readlines()
        for i in range(len(a))[2::2]:
            self.items_2.append((a[i].strip(), a[i+1].strip()))
        open_file.close()

# 确定系统编码方式为utf-8
reload(sys)
sys.setdefaultencoding('utf-8')

# 先检测缓存和下载文件夹
if not os.path.exists(u'下载'):
    os.makedirs(u'下载')
if not os.path.exists(u'缓存'):
    os.makedirs(u'缓存')

a = GCW()
a.start()

























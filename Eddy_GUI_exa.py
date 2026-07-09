# -*- coding: utf-8 -*-
"""
Created on Fri May 15 11:17:20 2015

@author: Leo
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 10:42:19 2015

@author: zhanghua
"""
import sys
import matplotlib.backends.backend_tkagg
from scipy.special import _ufuncs_cxx
from scipy.sparse.csgraph import _validation
import  multiprocessing
from PyQt4 import QtCore, QtGui
import make_eddy_track_AVISO_nc as eddy
from collections import OrderedDict
import datetime
import pdb

#import matplotlib.backends.backend_tkagg
class HBox(QtGui.QHBoxLayout):
    def __init__(self):
        super(HBox,self).__init__()
        self.setDirection(QtGui.QBoxLayout.RightToLeft)
        self.addStretch(1)
        
#自定义竖直层从上到下排列控件
class VBox(QtGui.QVBoxLayout):
    def __init__(self):
        super(VBox,self).__init__()
        self.setDirection(QtGui.QBoxLayout.BottomToTop)
        self.addStretch(1)
        
#自定义按钮，字体用微软雅黑
class Button(QtGui.QPushButton):
    def __init__(self,title,parent = None):
        super(Button,self).__init__(title,parent)
        self.setFont(QtGui.QFont("微软雅黑",11))
        
#自定义标签，主要是字号
class Label(QtGui.QLabel):
    def __init__(self,parent):
        super(Label,self).__init__(parent)
        self.setFont(QtGui.QFont("微软雅黑",11))
        
#自定义编辑框
class LineEdit(QtGui.QLineEdit):
    def __init__(self,parent = None,objectname = "#"):
        super(LineEdit,self).__init__(parent)
        self.setFont(QtGui.QFont("微软雅黑",11))
        self.setFixedWidth(150)
        self.setFixedHeight(25)
        self.setObjectName(objectname)
        
#自定义下拉列表
class ComboBox(QtGui.QComboBox):
    def __init__(self,parent = None,Items = None,objectname = "#"):
        super(ComboBox,self).__init__(parent = None)
        self.setFont(QtGui.QFont("微软雅黑",11))
        self.setFixedWidth(150)
        self.setFixedHeight(25)
        if Items != None:
            self.addItems(Items)
        self.setCurrentIndex(0)
        self.setObjectName(objectname)
        
#自定义复选框
class CheckBox(QtGui.QCheckBox):
    def __init__(self,parent = None):
        super(CheckBox,self).__init__(parent)
        self.setFont(QtGui.QFont("微软雅黑",11))
        self.setFixedHeight(25)
        self.setChecked(True)
      
class mainfram(QtGui.QWidget):
    MESSAGE = "<p>涡旋识别完成</p>"       
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self)
        self.resize(400, 700)
        self.setWindowTitle("海洋涡旋识别")
        self.setWindowIcon(QtGui.QIcon("single.jpg"))

        
        file_button = Button("",self)
        file_button.setIcon(QtGui.QIcon("Icon/OpenFile.png"))
        self.file_edit = LineEdit(self)
        self.file_edit.setReadOnly(True)
        self.file_edit.setFixedWidth(300)
#        self.StatusBar = QtGui.QMainWindow.statusBar()
#        ok_button = Button("确定",self)
#        self.cancel_button = Button("退出",self)
        
        eddy_rangeLabel=Label("识别范围")
        self.eddy_range_combobox = ComboBox(self,['*','Kuroshio Current','North Indian Ocean','South China Sea','West Pacific','Specific area','Global Ocean'])
        
        pool_Label=Label("进程池容量大小")
        self.pool_Label=LineEdit('2')
       
        
        pad_Label=Label("块与块间重叠部分度数")
        self.pad_Label=LineEdit('10')
        
        m_block_num_Label=Label("经向块数")
        self.m_block_num=LineEdit('8')
        
        z_block_num_Label=Label("纬向块数")
        self.z_block_num=LineEdit('5')
        
        
        
        filter_m_kernel_Label=Label("经向滤波核大小(度)")
        self.filter_m_kernel=LineEdit('20')
        
        filter_z_kernel_Label=Label("纬向滤波核大小(度)")
        self.filter_z_kernel=LineEdit('10')
        filter_kernel=Label("10-50")
        
        eddy_min_radius_Label=Label("涡旋像素大小")
        self.eddy_min_radius_Label=LineEdit('2')
        
        eddy_max_radius_Label=Label("到")
        self.eddy_max_radius_Label=LineEdit('100000')
        eddy_radius=Label("0-100000")
        
        
        #eddy_radius=Label("0-10")
        ac_effect_color_Label=Label("暖涡有效边界颜色")
        self.ac_effect_color_combobox= ComboBox(self,['red','green','blue','white','pink','black','yellow'])
        
        accolLabel=Label("暖涡最大地转流边界颜色")
        self.accol_combobox= ComboBox(self,['pink','green','blue','white','red','black','yellow'])
        
        accore_colLabel=Label("暖涡涡心颜色")
        self.accore_col_combobox=ComboBox(self,['black','red','green','blue','white','pink','yellow'])
        
        cc_effect_color_Label=Label("冷涡有效边界颜色")
        self.cc_effect_color_combobox= ComboBox(self,['blue','red','green','white','pink','black','yellow'])
        
        cccolLabel=Label("冷涡最大地转流边界颜色")
        self.cccol_combobox=ComboBox(self,['green','red','blue','white','pink','black','yellow'])
        
        cccore_colLabel=Label("冷涡涡心颜色")
        self.cccore_combobox=ComboBox(self,['black','red','green','blue','white','pink','yellow'])
        
        seed_sizeLabel=Label("涡心大小（像素）")
        self.seed_size=LineEdit('1')
        seed_sizewarn=Label("10-50")
        
        line_widthLabel=Label("边界宽度（像素）")
        self.line_width=LineEdit('0.1')
        line_widthwarn=Label("0-5")
        
        dpiLabel=Label("dpi(分辨率）")
        self.dpi=LineEdit('500')        
        dpiwarn=Label("500-1000")     
        
        add_eddyfig=Label("是否生成图片:")
        self.add_eddyfig_combobox = ComboBox(self,['no','yes'])
        
        add_sla_Label=Label("是否加SLA底图:")
        self.add_sla_combobox = ComboBox(self,['no','yes'])
        
        add_mask_Label=Label("是否生成涡旋的mask:")
        self.add_mask_combobox = ComboBox(self,['no','yes'])
        
        self.mainbutton2 = Button("输出文件路径")
        self.mainlabel2=LineEdit("")
        
#        self.mainbutton1 = Button("打开文件")
#        self.mainlabe1=LineEdit("")
#        self.mainlabe1.setReadOnly(True)

        #self.mainbutton3 = Button("识别涡旋")
        self.ok_button = Button("确定",self)
        self.cancel_button = Button("退出",self)
#        self.progressBAR=QtGui.QProgressBar()  #进度条
#        self.progressBAR.setFixedWidth(350)
        file_hbox = HBox()
        file_hbox.addWidget(self.file_edit)
        file_hbox.addWidget(file_button)
        

        grid = QtGui.QGridLayout()
        
                
#        grid.addWidget(self.mainbutton1, 0, 0)
#        grid.addWidget(self.mainlabe1, 0, 1)
  
        
        
        grid.setSpacing(15)
        grid.addWidget(eddy_rangeLabel, 1, 0)
        grid.addWidget(self.eddy_range_combobox, 1, 1)
        
        grid.addWidget(pool_Label,2,0)
        grid.addWidget(self.pool_Label,2,1) 
        grid.addWidget(pad_Label,2,2)
        grid.addWidget(self.pad_Label,2,3) 
        
        grid.addWidget(m_block_num_Label,3,0)
        grid.addWidget(self.m_block_num,3,1) 
        
        grid.addWidget(z_block_num_Label,3,2)
        grid.addWidget(self.z_block_num,3,3) 
        
        grid.addWidget(filter_m_kernel_Label, 4, 0)
        grid.addWidget(self.filter_m_kernel, 4, 1)
        
        grid.addWidget(filter_z_kernel_Label,4,2)
        grid.addWidget(self.filter_z_kernel, 4,3)  
        grid.addWidget(filter_kernel, 4, 4)
        
        grid.addWidget(eddy_min_radius_Label,5,0)
        grid.addWidget(self.eddy_min_radius_Label, 5,1) 
        grid.addWidget(eddy_max_radius_Label,5,2)
        grid.addWidget(self.eddy_max_radius_Label, 5,3) 
        grid.addWidget(eddy_radius, 5, 4)

        #pool_Label
        digramgrid = QtGui.QGridLayout()
        digramgrid.setSpacing(15)
        digramgrid.addWidget(ac_effect_color_Label,5,0)
        digramgrid.addWidget(self.ac_effect_color_combobox, 5,1)
        digramgrid.addWidget(cc_effect_color_Label,5,2)
        digramgrid.addWidget(self.cc_effect_color_combobox,5,3) 
        
        digramgrid.addWidget(accolLabel,6,0)
        digramgrid.addWidget(self.accol_combobox, 6,1)    
        digramgrid.addWidget(cccolLabel,6,2)
        digramgrid.addWidget(self.cccol_combobox, 6,3)
        
        digramgrid.addWidget(accore_colLabel,7,0)
        digramgrid.addWidget(self.accore_col_combobox, 7,1) 
        digramgrid.addWidget(cccore_colLabel,7,2)
        digramgrid.addWidget(self.cccore_combobox,7,3)          
        
        
        digramgrid.addWidget(seed_sizeLabel, 8, 0)
        digramgrid.addWidget(self.seed_size, 8, 1)
        digramgrid.addWidget(seed_sizewarn, 8, 2)
        
        
        digramgrid.addWidget(line_widthLabel, 9, 0)
        digramgrid.addWidget(self.line_width, 9, 1)
        digramgrid.addWidget(line_widthwarn, 9, 2)
        
        digramgrid.addWidget(dpiLabel, 10, 0)
        digramgrid.addWidget(self.dpi, 10, 1)
        digramgrid.addWidget(dpiwarn, 10, 2)

        digramgrid.addWidget(add_eddyfig, 11, 0)
        digramgrid.addWidget(self.add_eddyfig_combobox, 11, 1)
        
        digramgrid.addWidget(add_sla_Label, 12, 0)
        digramgrid.addWidget(self.add_sla_combobox, 12, 1)
        
        digramgrid.addWidget(add_mask_Label, 13, 0)
        digramgrid.addWidget(self.add_mask_combobox, 13, 1)

        digramgrid.addWidget(self.mainbutton2, 13, 0)
        digramgrid.addWidget(self.mainlabel2,13,1) 
        
        #digramgrid.addWidget(self.file_button,14,1)
        digramgrid.addWidget(self.ok_button,15,2)  
        digramgrid.addWidget(self.cancel_button,15,3)
#        grid.addWidget(self.progressBAR,13,0,1,20)
        vbox = VBox()
        vbox.setSpacing(10)
        
        vbox.addLayout(digramgrid)
        vbox.addWidget(Label("--------------------------------------------------------出图相关属性信息 --------------------------------------------------------"))
        vbox.addLayout(grid)
        vbox.addWidget(Label("--------------------------------------------------------涡旋识别属性信息  --------------------------------------------------------"))
        vbox.addLayout(file_hbox)
        vbox.addWidget(Label("请选择文件"))
        self.setLayout(vbox)
        
        file_button.clicked.connect(self.getopenncfilename)
        self.mainbutton2.clicked.connect(self.getoutfilename)
        self.ok_button.clicked.connect(self.Eddy_detect)
        self.connect(self.cancel_button,QtCore.SIGNAL("clicked()"),QtCore.SLOT("close()"))

    def getopenncfilename(self):
        options = QtGui.QFileDialog.DontResolveSymlinks | QtGui.QFileDialog.ShowDirsOnly
        fileName  = QtGui.QFileDialog.getExistingDirectory(self,"QFileDialog.getExistingDirectory()",
                     self.file_edit.text(), options)

        self.openfileName=fileName
        if fileName:
            self.file_edit.setText(fileName)


    def getoutfilename(self):
        options = QtGui.QFileDialog.DontResolveSymlinks | QtGui.QFileDialog.ShowDirsOnly
        fileName  = QtGui.QFileDialog.getExistingDirectory(self,"QFileDialog.getExistingDirectory()",
                     self.mainlabel2.text(), options)

        self.outfileName=fileName
        if fileName:
            self.mainlabel2.setText(fileName)    
    
    def Eddy_detect(self):
        print(datetime.datetime.now())
        openfile=str(self.openfileName)+'/'   #打开文件
        outfile=str(self.outfileName)+'/'   #输出文件
        eddy_location=self.eddy_range_combobox.currentText() #涡旋识别范围
        ac_eddy_edge_color=self.accol_combobox.currentText() #暖涡边界颜色
        cc_eddy_edge_color=self.cccol_combobox.currentText() #冷涡边界颜色
        ac_effect_edge_color=self.ac_effect_color_combobox.currentText()#暖涡有效边界颜色
        cc_effect_edge_color=self.cc_effect_color_combobox.currentText()#冷涡有效边界颜色
        ac_seed_color=self.accore_col_combobox.currentText() #暖涡涡心颜色
        cc_seed_color=self.cccore_combobox.currentText()  #冷涡涡心颜色
        if_add_eddyfig=self.add_eddyfig_combobox.currentText() #是否添加SLA底图
        if_add_slabg=self.add_sla_combobox.currentText() #是否添加SLA底图
        if_add_eddymask=self.add_mask_combobox.currentText() 
        m_block_num =int(self.m_block_num.text())
        z_block_num=int(self.z_block_num.text())
        
        out_range=float(self.pad_Label.text())
#        out_range2=float(self.pad_Label.text())
        seed_size=self.seed_size.text()  #涡心大小
        line_width=self.line_width.text()  #边界线宽
        dpi=self.dpi.text()  #dpi
        #滤波核的大小
        z_kernel=float(self.filter_z_kernel.text())/(0.25*8)
        m_kernel=float(self.filter_m_kernel.text())/(0.25*8)
        #涡旋半径范围（度）
        eddy_min_radius=float(self.eddy_min_radius_Label.text())
        eddy_max_radius=float(self.eddy_max_radius_Label.text())
        #将半径转换为像素个数
        eddy_pixel_num_range= [int(eddy_min_radius),int(eddy_max_radius)]
        
        #定义进程池大小
        pool_size=int(self.pool_Label.text())
        
        eddy_select_info=OrderedDict([('inputfile', str(openfile)),
                                      ('eddy_location',str(eddy_location)),
                                      ('ac_eddy_edge_color',str(ac_eddy_edge_color)),
                                      ('cc_eddy_edge_color',str(cc_eddy_edge_color)),
                                      ('ac_effect_edge_color',ac_effect_edge_color),
                                      ('cc_effect_edge_color',cc_effect_edge_color),
                                      ('line_width',float(line_width)),
                                      ('ac_seed_color',str(ac_seed_color)),
                                      ('cc_seed_color',str(cc_seed_color)),
                                      ('seed_size',float(seed_size)),
                                      ('dpi',int(dpi)),
                                      ('if_add_eddyfig',if_add_eddyfig),
                                      ('if_add_slabg',if_add_slabg),
                                      ('if_add_eddymask',if_add_eddymask),  
                                      ('outfile',str(outfile)),
                                      ('m_kernel',m_kernel),
                                      ('z_kernel',z_kernel),
                                      ('pool_size',pool_size),
                                      ('eddy_pixel_num_range',eddy_pixel_num_range),
                                      ('m_block_num',m_block_num), 
                                      ('z_block_num',z_block_num),
                                      ('out_range',out_range)
                                      
                                ])
                              
        eddy.gloabal_eddy_multi_detect(eddy_select_info)
        print (eddy_select_info)
        QtGui.QMessageBox.information(self,"Messager", mainfram.MESSAGE)
        
    
        
if __name__ == '__main__':
    
    multiprocessing.freeze_support()
    app = QtGui.QApplication(sys.argv)
    main = mainfram()       
    main.show()
    sys.exit(app.exec_())  
    
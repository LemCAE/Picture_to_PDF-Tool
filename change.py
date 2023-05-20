import fitz
import os
abs_dir=os.getcwd () #获得该文件所处的绝对路径
filename= os.path.basename (abs_dir)  

img_path = abs_dir
doc = fitz.open()
end = int(input('end:')) + 1

for i in range(0,end):
	n = str(i).rjust(3,'0') #格式化
	img = n + '.jpg' #文件名
	img_file = img_path + '\\' + img #地址
	imgdoc = fitz.open(img_file)
	pdfbytes = imgdoc.convertToPDF()
	pdf_name = str(i) + '.pdf'
	imgpdf = fitz.open(pdf_name, pdfbytes)
	doc.insertPDF(imgpdf)
doc.save('%s.pdf' % filename)
doc.close()
package com.example.demo.web;

import com.example.demo.utils.CSVUtil;
import com.example.demo.utils.FTPUtil;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import javax.servlet.http.HttpServletRequest;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.UUID;

/**
 * 测试controller
 *
 * @author dzm
 * @create 2019-02-21 14:09
 **/
@RestController
public class TestController {
    @Autowired
    private FTPUtil ftpUtil;
    private final Logger logger = LoggerFactory.getLogger(TestController.class);



    @PostMapping(value = "/upload/file")
    public void uploadFile(HttpServletRequest request) throws Exception {
        boolean b = ftpUtil.isExsits("aa/bb/eed641bc-884b-45cf-ae68-b374f306c818.csv");
        if(b){
            System.out.println("文件已经存在ftp服务器");
            return;
        }

        CSVUtil.writeCSV();
        //指定存放上传文件的目录
        String fileDir = "C:\\ftpfile\\img3";
        File dir = new File(fileDir);

        //判断目录是否存在，不存在则创建目录
        if (!dir.exists()){
            dir.mkdirs();
        }
        File inputFile = new File("C:/Users/dzm/Desktop/cp/cp.csv");
        FileInputStream fileInputStream = new FileInputStream(inputFile);
        MultipartFile multipartFile = new MockMultipartFile("copy"+inputFile.getName(),inputFile.getName(),"text/plain",fileInputStream);
        String originalFileName = multipartFile.getOriginalFilename();
        String suffix = originalFileName.substring(originalFileName.lastIndexOf('.'));
        //2、使用UUID生成新文件名
        String newFileName = UUID.randomUUID() + suffix;

        //生成文件
        //        C:\ftpfile\img  sdasdasd.jpg
        File file = new File(dir, newFileName);

        //传输内容
        try {
            multipartFile.transferTo(file);
            System.out.println("上传文件成功！");
        } catch (IOException e) {
            System.out.println("上传文件失败！");
            e.printStackTrace();
        }

        //至此，文件已经传到了程序运行的服务器上。
        //下面是这篇博客的重点

        //上传至ftp服务器
        //1、上传文件
        String [] strings = new String[2];
        strings[0] = "aa";
        strings[1] = "bb";
        if (ftpUtil.uploadToFtp(file,strings)){
            System.out.println("上传至ftp服务器！");
        }else {
            System.out.println("上传至ftp服务器失败!");
        }
//        //2、删除本地文件
        file.delete();

    }

}

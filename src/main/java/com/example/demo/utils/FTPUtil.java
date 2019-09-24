package com.example.demo.utils;

import lombok.extern.slf4j.Slf4j;
import org.apache.commons.net.ftp.FTP;
import org.apache.commons.net.ftp.FTPClient;
import org.apache.commons.net.ftp.FTPFile;
import org.apache.commons.net.ftp.FTPReply;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.*;

/**
 * 时间转换工具类
 *
 * @author dzm
 * @date 2018年7月31日
 */
@Slf4j
@Component
public class FTPUtil {

    @Value("${ftp.username}")
    private  String username;
    @Value("${ftp.password}")
    private  String password;
    @Value("${ftp.host}")
    private  String host;
    private static FTPClient ftp;

    private  static FTPClient getFTPClient(String host, String username, String password)throws IOException{
        if(ftp!=null){
            return ftp;
        }
        FTPClient ftpClient = new FTPClient();
        try {
            int reply;
            //连接ftp服务器 参数填服务器的ip
            ftpClient.connect(host);
            //进行登录 参数分别为账号 密码
            ftpClient.login(username,password);
            reply = ftpClient.getReplyCode();
            if (!FTPReply.isPositiveCompletion(reply)) {
                ftpClient.disconnect();
            }
            ftp = ftpClient;
        } catch (IOException e) {
            throw e;
        }
        return ftp;
    }


    /***
     * 判断文件是否存在
     * @param ftpPath
     * @return
     */
    public  boolean isExsits(String ftpPath){
        try {
            FTPClient ftpx = getFTPClient( host,  username,  password);
            FTPFile[] files =ftpx.listFiles(ftpPath);
            if(files!=null&&files.length>0){
                log.info("files size:"+files[0].getSize());
                return true;
            }else {
                return false;
            }
        } catch (IOException e) {
            //重新连接一次，可以么？
            try {
                Thread.sleep(1000);
            } catch (Exception e1) {

            }
            log.info("重新连接....");
            ftp = null;
            return isExsits(ftpPath);
        }
    }

    public  boolean uploadToFtp(File file,String... fileDirectorys){
        try {
            FTPClient ftpClient = getFTPClient(host,username,password);
            String[] strings = fileDirectorys;
            for(String s : strings){
                //不存在就创建
                ftpClient.makeDirectory(s);
                //改变工作目录
                ftpClient.changeWorkingDirectory(s);
            }
            //设置文件类型为二进制文件
            ftpClient.setFileType(FTP.BINARY_FILE_TYPE);

            //开启被动模式（按自己如何配置的ftp服务器来决定是否开启）
            ftpClient.enterLocalPassiveMode();

            //上传文件 参数：上传后的文件名，输入流
            ftpClient.storeFile(file.getName(), new FileInputStream(file));
        } catch (IOException e) {
            log.error("上传文件ftp异常：{}",e);
            return false;
        }
        return true;
    }

    public InputStream downloadToFtp(String ftpFilePath)throws IOException{
        FTPClient ftpClient = getFTPClient(host,username,password);
        InputStream in = null;
        ftpClient.setControlEncoding("UTF-8"); // 中文支持
        ftpClient.setFileType(FTPClient.BINARY_FILE_TYPE);
        ftpClient.enterLocalPassiveMode();
        in = ftpClient.retrieveFileStream(ftpFilePath);
        if(in==null){
            throw new FileNotFoundException("文件不存在");
        }
        return in;
    }


}

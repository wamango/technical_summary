package com.example.demo.ftp;


import lombok.extern.slf4j.Slf4j;
import org.apache.commons.net.ftp.FTP;
import org.apache.commons.net.ftp.FTPClient;
import org.apache.commons.net.ftp.FTPFile;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.io.*;

/**
 * ftp
 */
@Slf4j
@Component
public class FTPUtil {
    @Autowired
    private FTPClientPool ftpClientPool;
    /***
     * 判断文件是否存在
     * @param ftpPath
     * @return
     */
    public boolean isExsits(String ftpPath)throws Exception{
        FTPClient ftpClient = null;
        try {
            ftpClient = ftpClientPool.borrowObject();
            FTPFile[] files = ftpClient.listFiles(ftpPath);
            if (files != null && files.length > 0) {
                return true;
            }
            return false;
        }catch (Exception e){
            log.error("判断文件是否存在，异常：{}",e);
            throw  e;
        }finally {
            try {
                ftpClientPool.returnObject(ftpClient);
            } catch (Exception e) {
                log.error("returnObject error:{}",e);
            }
        }
    }

    public boolean uploadToFtp(File file, String... fileDirectorys) {
        FTPClient ftpClient = null;
        try {
            ftpClient = ftpClientPool.borrowObject();
            ftpClient.setControlEncoding("UTF-8");
            String[] strings = fileDirectorys;
            for (String s : strings) {
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
            FileInputStream fileInputStream = new FileInputStream(file);
            ftpClient.storeFile(file.getName(), fileInputStream);
            ftpClient.changeWorkingDirectory("/");
            //上传成功，删除本地文件
            fileInputStream.close();
            file.delete();
        } catch (Exception e) {
            log.error("上传文件ftp异常：{}", e);
            return false;
        }finally {
            try {
                ftpClientPool.returnObject(ftpClient);
            } catch (Exception e) {
                log.error("returnObject error:{}",e);
            }
        }
        return true;
    }


    /**
     * 从ftp上下载
     *
     * @param ftpFilePath
     * @return
     * @throws IOException
     */
    public byte[] downloadToFtp(String ftpFilePath) throws Exception {
        FTPClient ftpClient = null;
        try {
            ftpClient = ftpClientPool.borrowObject();
            ftpClient.setControlEncoding("UTF-8"); // 中文支持
            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            InputStream in = ftpClient.retrieveFileStream(ftpFilePath);
            byte[] buffer = new byte[1024];
            int len = 0;
            while ((len = in.read(buffer)) != -1) {
                baos.write(buffer, 0, len);
            }
            byte[] b = baos.toByteArray();
            in.close();
            if (!ftpClient.completePendingCommand()) {
                ftpClient.logout();
            }
            return b;
        } catch (Exception e) {
            log.error("从ftp下载文件异常：{}", e);
            throw e;
        }finally {
            try {
                ftpClientPool.returnObject(ftpClient);
            } catch (Exception e) {
                log.error("returnObject error:{}",e);
            }
        }
    }
}

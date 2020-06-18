package com.example.demo.ftp;

import lombok.extern.slf4j.Slf4j;
import org.apache.commons.net.ftp.FTPClient;
import org.apache.commons.net.ftp.FTPReply;
import org.apache.commons.pool.PoolableObjectFactory;

import java.io.IOException;

@Slf4j
public class FTPClientFactory implements PoolableObjectFactory<FTPClient> {
    private  FTPClientConfigure config;
    //给工厂传入一个参数对象，方便配置FTPClient的相关参数
    public FTPClientFactory(FTPClientConfigure config){
        this.config=config;
    }

    /* (non-Javadoc)
     * @see org.apache.commons.pool.PoolableObjectFactory#makeObject()
     */
    @Override
    public FTPClient makeObject(){
        FTPClient ftpClient = new FTPClient();
        ftpClient.setConnectTimeout(config.getClientTimeout());
        try {
            ftpClient.connect(config.getHost(), config.getPort());
            int reply = ftpClient.getReplyCode();
            if (!FTPReply.isPositiveCompletion(reply)) {
                ftpClient.disconnect();
                log.warn("FTPServer refused connection");
                return null;
            }
            boolean result = ftpClient.login(config.getUsername(), config.getPassword());
            if (!result) {
                throw new RuntimeException("ftpClient登陆失败! userName:" + config.getUsername() + " ; password:" + config.getPassword());
            }
            ftpClient.setFileType(FTPClient.BINARY_FILE_TYPE);
            ftpClient.setBufferSize(1024);
            ftpClient.setControlEncoding(config.getEncoding());
            ftpClient.enterLocalPassiveMode();
            ftpClient.setRemoteVerificationEnabled(false);
        } catch (Exception e) {
            log.error("ftp 异常:{}",e);
        }
        return ftpClient;
    }

    /* (non-Javadoc)
     * @see org.apache.commons.pool.PoolableObjectFactory#destroyObject(java.lang.Object)
     */
    @Override
    public void destroyObject(FTPClient ftpClient) throws Exception {
        try {
            if (ftpClient != null && ftpClient.isConnected()) {
                ftpClient.logout();
            }
        } catch (IOException io) {
            io.printStackTrace();
        } finally {
            // 注意,一定要在finally代码中断开连接，否则会导致占用ftp连接情况
            try {
                ftpClient.disconnect();
            } catch (IOException io) {
                io.printStackTrace();
            }
        }
    }

    /* (non-Javadoc)
     * @see org.apache.commons.pool.PoolableObjectFactory#validateObject(java.lang.Object)
     */
    @Override
    public boolean validateObject(FTPClient ftpClient) {
        try {
            return ftpClient.sendNoOp();
        } catch (IOException e) {
            return false;
        }
    }
    @Override
    public void activateObject(FTPClient ftpClient) throws Exception {
    }
    @Override
    public void passivateObject(FTPClient ftpClient) throws Exception {

    }
}

package com.example.demo.ftp;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class FTPConfig {
    @Autowired
    private FTPClientConfigure ftpClientConfigure;
    @Bean
    public FTPClientFactory ftpClientFactory(){
        return new FTPClientFactory(ftpClientConfigure);
    }
    @Bean
    public FTPClientPool initFTPClientPool(FTPClientFactory ftpClientFactory) throws Exception {
        return new FTPClientPool(ftpClientFactory);
    }
}

package com.example.demo.ftp;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Data
@Component
@ConfigurationProperties(prefix = "ftp")
public class FTPClientConfigure {
    private String host;
    private int port;
    private String username;
    private String password;
    private String encoding="UTF-8";
    private int clientTimeout=1000;
}

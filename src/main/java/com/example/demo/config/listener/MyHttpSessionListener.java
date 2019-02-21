package com.example.demo.config.listener;

import org.springframework.stereotype.Component;

import javax.servlet.http.HttpSessionEvent;
import javax.servlet.http.HttpSessionListener;

/**
 * 监听类
 *
 * @author dzm
 * @create 2019-02-21 15:42
 **/
@Component
public class MyHttpSessionListener implements HttpSessionListener {

    public static int count = 0;
    @Override
    public void sessionCreated(HttpSessionEvent httpSessionEvent) {
        System.out.println("创建session");
        ++count;
    }

    @Override
    public void sessionDestroyed(HttpSessionEvent httpSessionEvent) {
        System.out.println("销毁session");
    }
}

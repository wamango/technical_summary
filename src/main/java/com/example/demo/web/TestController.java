package com.example.demo.web;

import com.example.demo.config.listener.MyHttpSessionListener;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpSession;

/**
 * 测试controller
 *
 * @author dzm
 * @create 2019-02-21 14:09
 **/
@RestController
public class TestController {
    private final Logger logger = LoggerFactory.getLogger(TestController.class);


    /**
     * 测试拦截器
     * @return
     */
    @GetMapping("/test")
    public String test() {
        return  "拦截器";
    }

    /**
     * 测试session监听器
     * @param request
     * @return
     */
    @GetMapping("/index")
    public Object index(HttpServletRequest request) {
        HttpSession session = request.getSession(true);
        session.setAttribute("dzm", "dzm");
        return  "index";
    }

    /**
     * 测试session监听器
     * @return
     */
    @GetMapping("/online")
    public Object online() {
        return  "当前在线人数：" + MyHttpSessionListener.count + "人";
    }
}

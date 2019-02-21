package com.example.demo.web;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 测试controller
 *
 * @author dzm
 * @create 2019-02-21 14:09
 **/
@RestController
public class TestController {

    @GetMapping(value = "/test")
    public String test(){
        return "ceshi";
    }
}

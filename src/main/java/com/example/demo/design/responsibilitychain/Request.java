package com.example.demo.design.responsibilitychain;

/**
 * 请求
 *
 * @author dzm
 * @create 2018-11-20 10:41
 **/
public class Request {

    private RequestType type;
    private String name;


    public Request(RequestType type, String name) {
        this.type = type;
        this.name = name;
    }


    public RequestType getType() {
        return type;
    }


    public String getName() {
        return name;
    }
}

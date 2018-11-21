package com.example.demo.design.responsibilitychain;


/**
 * 处理器
 *
 * @author dzm
 * @create 2018-11-20 10:35
 **/
public abstract class Handler {
    protected Handler successor;

    public Handler(Handler successor){
        this.successor = successor;
    }

    public abstract void handleRequest(Request request);
}

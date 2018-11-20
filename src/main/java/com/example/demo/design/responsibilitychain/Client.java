package com.example.demo.design.responsibilitychain;

/**
 * 责任链-客户端
 *
 * @author dzm
 * @create 2018-11-20 10:45
 **/
public class Client {
    public static void main(String[] args) {
        Handler handler1 = new ConcreteHandler1(null);
        Handler handler2 = new ConcreteHandler2(handler1);
        Handler handler3 = new ConcreteHandler3(handler2);

        Request request1 = new Request(RequestType.TYPE1, "request1");
        handler3.handleRequest(request1);

        Request request2 = new Request(RequestType.TYPE2, "request2");
        handler3.handleRequest(request2);

        Request request3 = new Request(RequestType.TYPE3, "request3");
        handler3.handleRequest(request3);
    }
}

package com.example.demo.design.responsibilitychain;



/**
 * 混合处理器3
 *
 * @author dzm
 * @create 2018-11-20 10:39
 **/
public class ConcreteHandler3 extends Handler {
    public ConcreteHandler3(Handler successor){
        super(successor);
    }

    @Override
    protected void handleRequest(Request request) {
        if (request.getType() == RequestType.TYPE3) {
            System.out.println(request.getName() + " is handle by ConcreteHandler3");
            return;
        }
        if (successor != null) {
            successor.handleRequest(request);
        }
    }
}

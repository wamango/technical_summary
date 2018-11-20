package com.example.demo.design.responsibilitychain;



/**
 * 混合处理器1
 *
 * @author dzm
 * @create 2018-11-20 10:39
 **/
public class ConcreteHandler1 extends Handler {
    public ConcreteHandler1(Handler successor){
        super(successor);
    }

    @Override
    protected void handleRequest(Request request) {
        if (request.getType() == RequestType.TYPE1) {
            System.out.println(request.getName() + " is handle by ConcreteHandler1");
            return;
        }
        if (successor != null) {
            successor.handleRequest(request);
        }
    }
}

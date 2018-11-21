package com.example.demo.design.responsibilitychain;



/**
 * 混合处理器2
 *
 * @author dzm
 * @create 2018-11-20 10:39
 **/
public class ConcreteHandler2 extends Handler {
    public ConcreteHandler2(Handler successor){
        super(successor);
    }

    @Override
    public void handleRequest(Request request) {
        if (request.getType() == RequestType.TYPE2) {
            System.out.println(request.getName() + " is handle by ConcreteHandler2");
            return;
        }
        if (successor != null) {
            successor.handleRequest(request);
        }
    }
}

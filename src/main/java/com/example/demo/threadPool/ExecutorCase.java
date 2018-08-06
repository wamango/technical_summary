package com.example.demo.threadPool;

import java.util.concurrent.*;

/**
 * java线程池例子
 *https://www.jianshu.com/p/87bff5cc8d8c
 * @author dzm
 * @create 2018-07-26 18:18
 **/
public class ExecutorCase {
//    private static Executor exector = Executors.newFixedThreadPool(10);

    //
//    public static void main(String[] args) {
//        for(int i=0;i<20;i++){
//            exector.execute(new Task());
//        }
//    }
//
//    static class Task implements Runnable{
//        @Override
//        public void run() {
//            //打印当前线程的名字
//            System.out.println(Thread.currentThread().getName());
//        }
//    }


    private static ExecutorService executor = Executors.newFixedThreadPool(10);
    public static void main(String[] args) {
        Future<String> future = executor.submit(new Task());
        System.out.println("do other things");
        try{
            //等待线程返回结果，没有时间限制
            String result = future.get();
            //等待1秒，超时没有返回抛出TimeOutException异常
//            String result = future.get(1,TimeUnit.SECONDS);
            System.out.println(result);
        }catch (Exception e){
            e.printStackTrace();
        }
    }

    /**
     * 任务类
     */
    static class Task implements Callable<String>{
        @Override
        public String call() throws Exception {
            try{
                TimeUnit.SECONDS.sleep(2);
            }catch (InterruptedException e){
                e.printStackTrace();
            }
            return "this is future case";
        }
    }
}

package com.example.demo.threadpool;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.concurrent.*;

/**
 * java线程池例子
 *https://www.jianshu.com/p/87bff5cc8d8c
 * @author dzm
 * @create 2018-07-26 18:18
 **/
public class ExecutorCase {
    private static Logger logger = LoggerFactory.getLogger(ExecutorCase.class);
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
   /* public static void main(String[] args) {
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
*/

    /**
     * 任务类添加
     */
    static class Task implements Callable<String>{

        /**
         * 任务回调方法
         * @return
         * @throws Exception
         */
        @Override
        public String call() throws Exception {
            try{
                TimeUnit.SECONDS.sleep(2);
            }catch (InterruptedException e){
                logger.error("回调异常{}",e);
            }
            return "this is future case";
        }
    }
}

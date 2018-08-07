package com.zcs.test.result;

import com.example.demo.result.ResponseInfo;

/**
 * 返回结果
 *
 * @author dzm
 * @create 2018-03-05 14:10
 **/
public class ResultInfo {
    /**
     * 成功
     * @return
     */
    public static ResponseInfo success(){
        return success(null);
    }

    /**
     * 成功
     * @param data
     * @param <T>
     * @return
     */
    public static <T>ResponseInfo<T> success(T data){
        return success("成功",data);
    }

    /**
     * 成功
     * @param message
     * @param data
     * @param <T>
     * @return
     */
    public static  <T>ResponseInfo<T> success(String message,T data){
        return result("0000",message,data);
    }

    /**
     * 失败
     * @return
     */
    public static ResponseInfo error(){
        return error("失败");
    }

    /**
     * 失败
     * @param message
     * @return
     */
    public static ResponseInfo error(String message){
        return error("1000",message);
    }

    /**
     * 失败
     * @param code
     * @param message
     * @return
     */
    public static ResponseInfo error(String code,String message){
        return result(code,message,null);
    }

    /**
     * 返回结果拼接
     * @param code
     * @param message
     * @param data
     * @param <T>
     * @return
     */
    public static <T>ResponseInfo<T> result(String code,String message,T data){
        ResponseInfo<T> body = new ResponseInfo<>();
        body.setRetCode(code);
        body.setMessage(message);
        body.setData(data);
        return body;
    }
}

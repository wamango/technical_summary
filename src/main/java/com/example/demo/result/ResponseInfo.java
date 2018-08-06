package com.example.demo.result;

import lombok.Data;

/**
 * 封装返回结果
 *
 * @author dzm
 * @create 2018-03-05 14:06
 **/
@Data
public class ResponseInfo<T>{
    /**错误码*/
    private String retCode;
    /**错误信息*/
    private String message;
    /**返回结果*/
    private T data;
}

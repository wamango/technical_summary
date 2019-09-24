//package com.example.demo.config.filter;
//
//import org.springframework.stereotype.Component;
//
//import javax.servlet.*;
//import javax.servlet.http.HttpServletRequest;
//import javax.servlet.http.HttpServletResponse;
//import javax.servlet.http.HttpServletResponseWrapper;
//import java.io.IOException;
//
///**
// * 过滤器
// *
// * @author dzm
// * @create 2019-02-21 16:07
// **/
//@Component
//public class MyFilter implements Filter {
//    @Override
//    public void init(FilterConfig filterConfig) throws ServletException {
//        System.out.println("----------------------->过滤器被创建");
//    }
//
//    @Override
//    public void doFilter(ServletRequest servletRequest, ServletResponse servletResponse, FilterChain filterChain) throws IOException, ServletException {
//        System.out.println(servletRequest.getParameter("name"));
//        HttpServletRequest hrequest = (HttpServletRequest)servletRequest;
//        HttpServletResponseWrapper wrapper = new HttpServletResponseWrapper((HttpServletResponse) servletResponse);
//        if(hrequest.getRequestURI().indexOf("/index") != -1 ||
//                hrequest.getRequestURI().indexOf("/online") != -1
//                ) {
//            filterChain.doFilter(servletRequest, servletResponse);
//        }else {
//            wrapper.sendRedirect("/test");
//        }
//    }
//
//    @Override
//    public void destroy() {
//        System.out.println("----------------------->过滤器被销毁");
//    }
//}

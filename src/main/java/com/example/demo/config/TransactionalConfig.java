package com.example.demo.config;

import com.google.common.collect.Lists;
import com.google.common.collect.Maps;
import org.springframework.aop.aspectj.AspectJExpressionPointcutAdvisor;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Component;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.TransactionDefinition;
import org.springframework.transaction.interceptor.*;

import java.util.Map;

/**
 * 事务拦截器
 * @author fjy
 */
@Component
public class TransactionalConfig {

    /**
     * 定义事务属性
     * @return
     */
    @Bean("txSource")
    public TransactionAttributeSource transactionAttributeSource(){
        //只读事务
        RuleBasedTransactionAttribute readOnly = new RuleBasedTransactionAttribute();
        readOnly.setReadOnly(true);
        readOnly.setPropagationBehavior(TransactionDefinition.PROPAGATION_NOT_SUPPORTED);
        //需要支持事务的
        RuleBasedTransactionAttribute required = new RuleBasedTransactionAttribute();
        required.setPropagationBehavior(TransactionDefinition.PROPAGATION_REQUIRED);
        required.setRollbackRules(Lists.newArrayList(new RollbackRuleAttribute(Exception.class)));
        required.setTimeout(10);

        Map<String,TransactionAttribute> paramMap = Maps.newHashMap();
        paramMap.put("add*",required);
        paramMap.put("update*",required);
        paramMap.put("insert*",required);
        paramMap.put("*", readOnly);
        NameMatchTransactionAttributeSource source = new NameMatchTransactionAttributeSource();
        source.setNameMap(paramMap);
        return source;
    }

    /**
     * 事务拦截
     * @param tx
     * @return
     */
    @Bean("txAdvice")
    public TransactionInterceptor transactionInterceptor(PlatformTransactionManager tx){
        return new TransactionInterceptor(tx,transactionAttributeSource());
    }

    /**
     * 事务切面
     * @param txAdvice
     * @return
     */
    @Bean
    public AspectJExpressionPointcutAdvisor pointcutAdvisor(TransactionInterceptor txAdvice){
        AspectJExpressionPointcutAdvisor pointcutAdvisor = new AspectJExpressionPointcutAdvisor();
        pointcutAdvisor.setAdvice(txAdvice);
        pointcutAdvisor.setExpression("execution (* com.zcs.test.service.*.*(..))");
        return pointcutAdvisor;
    }

}

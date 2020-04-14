import java.util.LinkedList;
import java.util.Queue;

class MyStack {

    Queue<Integer> q;
    int lastNum;
    /** Initialize your data structure here. */
    public MyStack() {
        q = new LinkedList<>();
    }

    /** Push element x onto stack. */
    public void push(int x) {
        q.offer(x);
        lastNum = x;
    }

    /** Removes the element on top of the stack and returns that element. */
    public int pop() {
        int size = q.size();
        while(size>2){
            q.offer(q.poll());
            size--;
        }
        lastNum = q.peek();
        q.offer(q.poll());
        return q.poll();
    }

    /** Get the top element. */
    public int top() {
        return lastNum;
    }

    /** Returns whether the stack is empty. */
    public boolean empty() {
        return q.isEmpty();
    }

    public static void main(String[] args) {

    }
}
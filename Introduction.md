# Introduction #

  * **What is pyvim?**
pyvim is a python package, which is made to programming the vim internal function.


  * **What can pyvim do for me?**
pyvim wraps the vim element, such as buffer and window, into Object-Oriented python object pvBuffer/pvWindow . You can create, destroy and manipulate them via the python interface.


And as well, pyvim wraps the autocmd & keymap into an event-like system -- pvEvent.You can bind a python object to this event as a "observer".


And until now, pyvim is already implemented a tree buffer ( pvTreeBuffer ) and list/tab buffer ( pvLinearBuffer ).It is easy for you to construct a selectable list buffer or even tree buffer with few python code.


  * **What functions does the pyvim implement until now?**

1._pvBuffer_ & _pvWindow_ : manipulate the vim internal buffer and window

2._pvEvent_ : wrap the autocmd & keymap

3._pvString_ : manage the unicode string and vim internal string

4._pvModel_  : use Model-View(buffer) to implemented the data for functional buffer

5._pvTreeBuffer_ & _pvLinearBuffer : implemented the functional buffer_

6.some other




# More Detail #

For more detail about each function, please refer the relevant link:

  * pvBuffer
  * pvWindow
  * pvWinSplitter
  * pvAutocmdEvent
  * pvKeymapEvent
  * pvAbstractModel
  * pvTreeBuffer
  * pvLinearBuffer
  * pvString